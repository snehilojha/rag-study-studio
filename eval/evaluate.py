#!/usr/bin/env python
"""Retrieval evaluation for this stack.

Scores Qdrant retrieval against the hand-annotated question set in
questions.json, using Precision@K and Mean Reciprocal Rank.

Two variants are measured on every run:

    retrieval   search_chunks(top_k=K)              -- what the vector store finds
    reranked    search_chunks(top_k=N) -> rerank(K) -- what the app actually shows

The delta between them is what the cross-encoder buys. The old FAISS harness in
reference/ had no reranker and could not measure this.

Relevance is keyword presence, not human grading -- cheap enough to run on every
change, which is the whole point. A chunk counts as relevant when at least
MATCH_THRESHOLD of the question's keyword roots appear in its text.

The metric definitions, the 0.67 threshold, and the 5-character root truncation
are carried over from reference/evaluate_faiss.py (rag_assistant, archived
2026-08-23). Nothing else from that file transfers -- see eval/README.md.

Every result file records the config that produced it. Runs are only comparable
when that config matches; --compare enforces this rather than trusting you to
remember.

Usage:
    python eval/evaluate.py --questions eval/questions.json
    python eval/evaluate.py --questions eval/questions.json --debug
    python eval/evaluate.py --questions eval/questions.json --book-id 1
    python eval/evaluate.py --questions eval/questions.json --output eval/results/baseline.json
    python eval/evaluate.py --questions eval/questions.json --compare eval/results/baseline.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"

# Relevance thresholds -- carried over from the archived harness.
# 0.67 == at least 2 of 3 keywords. Strict AND-matching was too brittle: one
# rare or inflected keyword produced false negatives on correct retrievals.
MATCH_THRESHOLD = 0.67
# 5 chars catches most useful roots without over-truncating short words:
# "generalizes" -> "gener", "branching" -> "branc", "bayes" -> "bayes".
MIN_ROOT_LEN = 5

METRICS = ("p1", "p3", "p5", "mrr")
VARIANTS = ("retrieval", "reranked")


# ---------------------------------------------------------------------------
# Relevance scoring -- no dependency on how the chunks were retrieved
# ---------------------------------------------------------------------------

def keyword_root(kw: str) -> str:
    """Truncate a keyword to a root for stem-aware substring matching."""
    return kw.lower()[:min(MIN_ROOT_LEN, len(kw))]


def chunk_matches(chunk: dict, keywords: list[str]) -> bool:
    """True when enough of the question's keyword roots appear in the chunk."""
    text = chunk.get("text", "").lower()
    required = max(1, round(len(keywords) * MATCH_THRESHOLD))
    matched = sum(1 for kw in keywords if keyword_root(kw) in text)
    return matched >= required


def reciprocal_rank(chunks: list[dict], keywords: list[str]) -> float:
    """1 / (1-based rank of the first relevant chunk), or 0.0 if none match."""
    for i, chunk in enumerate(chunks):
        if chunk_matches(chunk, keywords):
            return 1.0 / (i + 1)
    return 0.0


def score(chunks: list[dict], keywords: list[str]) -> dict:
    """Per-question scores for one ranked list."""
    return {
        "p1": 1.0 if chunks and chunk_matches(chunks[0], keywords) else 0.0,
        "p3": 1.0 if any(chunk_matches(c, keywords) for c in chunks[:3]) else 0.0,
        "p5": 1.0 if any(chunk_matches(c, keywords) for c in chunks[:5]) else 0.0,
        "mrr": reciprocal_rank(chunks, keywords),
    }


# ---------------------------------------------------------------------------
# Retrieval -- through the application's own code path, deliberately
# ---------------------------------------------------------------------------

def retrieve_variants(
    query: str,
    *,
    book_id: int | None,
    top_k: int,
    retrieve_k: int,
    use_reranker: bool,
) -> dict[str, list[dict]]:
    """Return {variant: ranked chunk dicts} for one query.

    Both variants embed through services.embedder, so a change there (the
    asymmetric query prefix, for one) shows up in these numbers automatically.
    """
    from services.embedder import embed_query
    from services.vector_store import search_chunks

    vector = embed_query(query)

    out: dict[str, list[dict]] = {
        "retrieval": search_chunks(query_vector=vector, book_id=book_id, top_k=top_k)
    }

    if not use_reranker:
        return out

    from services.reranker import rerank

    candidates = search_chunks(query_vector=vector, book_id=book_id, top_k=retrieve_k)
    if not candidates:
        out["reranked"] = []
        return out

    ranked_texts = rerank(query, [c["text"] for c in candidates], top_k=top_k)

    # rerank() returns bare strings; map them back to their payloads the way
    # qa_service does. Identical chunk texts would collide here -- with
    # overlapping chunks that is possible, so count it if it ever matters.
    by_text = {c["text"]: c for c in candidates}
    out["reranked"] = [by_text[t] for t in ranked_texts if t in by_text]
    return out


# ---------------------------------------------------------------------------
# Provenance -- a result file nobody can misread later
# ---------------------------------------------------------------------------

def collect_config(args) -> dict:
    """Snapshot everything that would invalidate a comparison."""
    from config import settings

    reranker_model = None
    if args.rerank:
        from services.reranker import RERANKER_MODEL
        reranker_model = RERANKER_MODEL

    cfg = {
        "embedding_model": settings.EMBEDDING_MODEL,
        "reranker_model": reranker_model,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "top_k": args.top_k,
        "retrieve_k": args.retrieve_k,
        "book_id_filter": args.book_id,
        "match_threshold": MATCH_THRESHOLD,
        "min_root_len": MIN_ROOT_LEN,
    }

    try:
        from services.vector_store import COLLECTION_NAME, _get_client
        cfg["collection"] = COLLECTION_NAME
        cfg["points"] = _get_client().count(COLLECTION_NAME).count
    except Exception as exc:  # noqa: BLE001 -- provenance is best-effort
        cfg["collection_error"] = str(exc)

    try:
        from sqlmodel import Session, select
        from database import engine
        from models import Book
        with Session(engine) as session:
            cfg["corpus"] = [
                {"id": b.id, "title": b.title, "status": b.status.value}
                for b in session.exec(select(Book).order_by(Book.id)).all()
            ]
    except Exception as exc:  # noqa: BLE001
        cfg["corpus_error"] = str(exc)

    return cfg


# Config keys that make two runs incomparable if they differ.
BLOCKING_KEYS = (
    "embedding_model", "chunk_size", "chunk_overlap",
    "top_k", "book_id_filter", "match_threshold", "min_root_len",
)


def compare(current: dict, prior_path: Path) -> None:
    """Print a delta table, refusing to imply comparability that isn't there."""
    with prior_path.open(encoding="utf-8") as f:
        prior = json.load(f)

    if "metrics" not in prior or "config" not in prior:
        print(f"\n! {prior_path} is not a result file from this harness -- not comparing.")
        print("  Historical numbers in eval/results/ came from FAISS + all-mpnet-base-v2")
        print("  on a different corpus. They are not a baseline for this stack.")
        return

    drift = [
        (k, prior["config"].get(k), current["config"].get(k))
        for k in BLOCKING_KEYS
        if prior["config"].get(k) != current["config"].get(k)
    ]

    prior_books = {b["id"] for b in prior["config"].get("corpus", [])}
    current_books = {b["id"] for b in current["config"].get("corpus", [])}
    corpus_changed = prior_books != current_books

    print(f"\n-- vs {prior_path.name} ({prior.get('run_at', 'unknown date')}) " + "-" * 12)

    if drift or corpus_changed:
        print("\n  ! CONFIG DRIFT -- these runs measure different systems.")
        for key, was, now in drift:
            print(f"    {key}: {was} -> {now}")
        if corpus_changed:
            print(f"    corpus: books {sorted(prior_books)} -> {sorted(current_books)}")
        print("    The deltas below are not attributable to any single change.\n")

    print(f"  {'metric':<8}{'prior':<10}{'current':<10}{'delta':<10}")
    print("  " + "-" * 36)
    for variant in VARIANTS:
        if variant not in prior["metrics"] or variant not in current["metrics"]:
            continue
        print(f"  [{variant}]")
        for m in METRICS:
            was = prior["metrics"][variant].get(m)
            now = current["metrics"][variant].get(m)
            if was is None or now is None:
                continue
            delta = now - was
            sign = "+" if delta >= 0 else ""
            print(f"  {m:<8}{was:<10.3f}{now:<10.3f}{sign}{delta:.3f}")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def evaluate(questions: list[dict], args) -> dict:
    variants = list(VARIANTS) if args.rerank else ["retrieval"]
    totals = {v: {m: [] for m in METRICS} for v in variants}
    per_question = []

    if args.debug:
        header = f"{'#':<4}"
        for v in variants:
            header += f"{v[:8] + '@1':<12}{v[:8] + '@5':<12}"
        print(f"\n{header}question")
        print("-" * 96)

    for i, item in enumerate(questions, start=1):
        query = item["question"]
        keywords = item["keywords"]

        results = retrieve_variants(
            query,
            book_id=args.book_id,
            top_k=args.top_k,
            retrieve_k=args.retrieve_k,
            use_reranker=args.rerank,
        )

        row = {"question": query, "keywords": keywords, "scores": {}}
        for v in variants:
            s = score(results[v], keywords)
            row["scores"][v] = s
            for m in METRICS:
                totals[v][m].append(s[m])

        per_question.append(row)

        if args.debug:
            line = f"{i:<4}"
            for v in variants:
                s = row["scores"][v]
                line += f"{('hit' if s['p1'] else '-'):<12}{('hit' if s['p5'] else '-'):<12}"
            print(f"{line}{query[:50]}")

            missed_everywhere = all(row["scores"][v]["p5"] == 0.0 for v in variants)
            if missed_everywhere:
                roots = [keyword_root(k) for k in keywords]
                top = results[variants[0]]
                preview = top[0]["text"][:110].replace("\n", " ") if top else "(nothing retrieved)"
                page = top[0].get("page_number") if top else None
                print(f"      roots={roots}")
                print(f"      top chunk (p.{page}): {preview}...")

    n = len(questions)
    metrics = {
        v: {m: (sum(totals[v][m]) / n if n else 0.0) for m in METRICS}
        for v in variants
    }
    return {"metrics": metrics, "questions": per_question, "n": n}


def print_metrics(result: dict) -> None:
    print("\n-- results " + "-" * 32)
    print(f"  {'metric':<8}" + "".join(f"{v:<12}" for v in result["metrics"]))
    print("  " + "-" * 32)
    for m in METRICS:
        label = "MRR" if m == "mrr" else f"P@{m[1]}"
        row = "".join(f"{result['metrics'][v][m]:<12.3f}" for v in result["metrics"])
        print(f"  {label:<8}{row}")

    if len(result["metrics"]) == 2:
        gains = {
            m: result["metrics"]["reranked"][m] - result["metrics"]["retrieval"][m]
            for m in METRICS
        }
        best = max(gains.values())
        verdict = "earns its place" if best > 0.02 else "is not measurably helping"
        print(f"\n  Reranker {verdict} on this corpus (best gain {best:+.3f}).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval quality against Qdrant.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--questions", default="eval/questions.json",
                        help="Question set JSON (default: eval/questions.json)")
    parser.add_argument("--book-id", type=int, default=None,
                        help="Restrict retrieval to one book (default: whole corpus)")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Ranked list length that gets scored (default: 5)")
    parser.add_argument("--retrieve-k", type=int, default=12,
                        help="Over-fetch depth before reranking; matches qa_service (default: 12)")
    parser.add_argument("--no-rerank", dest="rerank", action="store_false",
                        help="Skip the reranked variant (faster; retrieval only)")
    parser.add_argument("--output", default=None, help="Write results JSON here")
    parser.add_argument("--compare", default=None,
                        help="Prior result file from this harness to diff against")
    parser.add_argument("--debug", action="store_true",
                        help="Per-question hits, with keyword roots on a total miss")
    args = parser.parse_args()

    # Resolve user paths before the chdir below.
    questions_path = Path(args.questions).resolve()
    output_path = Path(args.output).resolve() if args.output else None
    compare_path = Path(args.compare).resolve() if args.compare else None

    if not questions_path.exists():
        print(f"error: no question set at {questions_path}", file=sys.stderr)
        return 2

    # backend/ uses absolute imports (`from config import settings`) and reads
    # its .env relative to the working directory, so run from there.
    sys.path.insert(0, str(BACKEND_DIR))
    os.chdir(BACKEND_DIR)

    with questions_path.open(encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Questions: {len(questions)} from {questions_path.name}")
    print("Loading models and connecting to Qdrant...")

    config = collect_config(args)
    corpus = config.get("corpus", [])
    ready = [b for b in corpus if b["status"] == "ready"]
    print(f"Corpus: {len(ready)} ready book(s), {config.get('points', '?')} points"
          + (f", filtered to book_id={args.book_id}" if args.book_id else ""))
    for b in ready:
        print(f"  [{b['id']}] {b['title'][:66]}")

    if not ready:
        print("\nerror: no books with status=ready -- ingest something first.", file=sys.stderr)
        return 1

    result = evaluate(questions, args)
    result = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": config,
        **result,
    }

    print_metrics(result)

    if compare_path:
        compare(result, compare_path)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nWrote {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
