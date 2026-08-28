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

## The harness

`evaluate.py` scores retrieval against this stack. Run it from the repo root:

```
python eval/evaluate.py --questions eval/questions.json --debug
python eval/evaluate.py --output eval/results/baseline.json
python eval/evaluate.py --compare eval/results/baseline.json
```

Requires Qdrant reachable at `QDRANT_URL` and at least one book with
`status=ready`. It scores retrieval only and never calls an LLM, so it runs even
while the generation path is broken.

Two variants are measured on every run:

| Variant | Path | Answers |
|---|---|---|
| `retrieval` | `search_chunks(top_k=5)` | What does the vector store find on its own? |
| `reranked` | `search_chunks(top_k=12)` then `rerank(5)` | What does the app actually show? |

The gap between them is the cross-encoder's contribution. The archived harness
had no reranker and could not measure it.

Queries embed through `services.embedder`, so changes there — the missing
asymmetric query prefix, for one — show up in the numbers without touching this
file.

## Comparing runs honestly

Every result file records the config that produced it: embedding model, chunk
size and overlap, `top_k`, the book filter, the relevance thresholds, and the
corpus. `--compare` checks that config against the current run and prints a
loud drift warning when they differ, because a delta across two different
systems is not attributable to anything.

Pointed at a file in `results/` that predates this harness, `--compare` refuses
outright.

## What was actually reused

Roughly 60 of the 229 lines in `reference/evaluate_faiss.py`:

- the metric definitions — P@1/3/5 and MRR by first relevant chunk
- `MATCH_THRESHOLD = 0.67` and `MIN_ROOT_LEN = 5`, and the reasoning behind
  them: strict AND-matching produced false negatives on correct retrievals
- keyword presence as the relevance signal, which is what makes the harness
  cheap enough to run on every change

Everything else was FAISS index loading, CLI plumbing, and per-book indices —
none of which map onto a single Qdrant collection with a payload filter.

One function was deliberately **not** ported. `print_comparison` hardcoded
`chunk_size == 384` and printed a delta against `all-mpnet-base-v2` numbers from
a different corpus. It produced a rigorous-looking comparison that meant
nothing. `--compare` is its replacement, and it fails loudly where the original
failed silently.

The real asset here was never the code — it was `questions.json`.

## Reference files

`reference/` stays for two things beyond the metric logic:

- `ingest_faiss.py` builds a global token stream with a parallel token-to-page
  map, so every chunk records the page it actually started on. That is the fix
  for the fabricated page numbers in `services/chunker.py`.
- `retriever_faiss.py` documents the asymmetric query-prefix requirement this
  project does not currently apply.

Neither runs against this repo.
