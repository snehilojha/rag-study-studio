# Retrieval Evaluation

Measures retrieval quality with Precision@K and Mean Reciprocal Rank against a
hand-annotated question set.

## Provenance

These artifacts came from the `rag_assistant` project (github.com/snehilojha/rag-assistant),
which was archived on 2026-08-23 and folded into this one. In that repo `eval/` was
gitignored, so `questions.json` and the baseline metrics existed only on local disk.
They are tracked here.

## Contents

| Path | What it is | State |
|---|---|---|
| `questions.json` | 20 questions with hand-annotated relevance keywords | Ready to use |
| `EXPERIMENTS.md` | Prior experiment log — chunk size and overlap sweeps | Historical |
| `results/rag_assistant_baseline.json` | Baseline metrics from the FAISS stack | Historical |
| `results/overlap_comparison.json` | Raw overlap sweep output | Historical |
| `reference/` | The original FAISS implementation | **Does not run against this repo** |

## Important: the historical numbers do not describe this system

`EXPERIMENTS.md` reports results measured on a different stack:

- `all-mpnet-base-v2` embeddings, 384-token chunks, FAISS `IndexFlatIP`, no reranker

This project runs `snowflake-arctic-embed-l` against Qdrant with a cross-encoder
reranker and LLM query rewriting. The conclusions do not transfer. Treat the file as a
record of *method*, not of *results*, and re-run the sweeps against this stack.

Two known caveats on the historical numbers:

1. The chunk-size experiment (Experiment 1) looks sound.
2. The overlap experiment (Experiment 2) ran with a broken monkey-patch that was fixed
   afterward without re-running the sweep. Treat those conclusions as unverified.

## Rewiring status

`reference/evaluate_faiss.py` is the original harness. The metric logic (P@K, MRR,
stem-truncated keyword matching) transfers as-is; the retrieval call does not.

To port it, replace the FAISS `retrieve()` call with `services.vector_store.search_chunks`
and drop the index-loading path — Qdrant handles persistence and per-book filtering.

`reference/ingest_faiss.py` is kept for a different reason: its `chunk_text` builds a
global token stream with a parallel token-to-page map, so every chunk records the page
it actually started on. That is the fix for the fabricated page numbers described in
`ROADMAP.md` (Tier 0, item 2).

`reference/retriever_faiss.py` documents the asymmetric query-prefix requirement that
this project's embedder currently does not apply (ROADMAP.md, Tier 0).
