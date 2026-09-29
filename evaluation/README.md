# Retrieval evaluation methodology

This folder separates a reproducible synthetic evaluation, a real-manual development experiment and a frozen holdout evaluation.

## Synthetic demo set

`questions.json` contains nine labelled questions for the three synthetic PDFs in `demo_docs/`. It verifies that the evaluation pipeline works on a fresh clone without redistributing third-party manuals.

```bash
python scripts/index_folder.py demo_docs
python scripts/evaluate.py \
  --cases evaluation/questions.json \
  --top-k 5 \
  --output evaluation/results.csv
```

## Real-manual development set

`real_questions.json` is a **development set**, not a final holdout test. It was built against a locally downloaded Siemens S7-1200 G2 system manual and inspected during retrieval development. The vendor PDF is intentionally excluded from version control.

The current labels use **multi-positive page ground truth** where more than one physical PDF page independently contains enough information to support the question. Three cases were adjudicated after manual inspection:

- `REAL-IP-01`: pages 224 and 246
- `REAL-S7-01`: pages 267 and 268
- `REAL-S7-02`: pages 268 and 269

The earlier labels are preserved in `real_questions_initial.json` for experiment traceability.

### Development results

| Metric | Dense | Hybrid |
| --- | ---: | ---: |
| Page Recall@1 | 0.467 | **0.667** |
| Page Recall@3 | 0.867 | **0.933** |
| Page Recall@5 | **0.933** | **0.933** |
| Page MRR | 0.672 | **0.800** |

Canonical result files:

- `real_results_dense_adjudicated.csv`
- `real_results_hybrid_adjudicated.csv`

Historical pre-adjudication outputs are retained as:

- `real_results_dense_initial_labels.csv`
- `real_results_hybrid_initial_labels.csv`

## Frozen holdout set

`holdout_questions.json` contains 12 questions from previously unused manual topics. Ground-truth pages were labelled before retrieval was run, and retrieval parameters were frozen before inspecting the results.

### Holdout results

| Metric | Dense | Hybrid |
| --- | ---: | ---: |
| Page Recall@1 | 0.750 | **0.833** |
| Page Recall@3 | 0.917 | **1.000** |
| Page Recall@5 | **1.000** | **1.000** |
| Page MRR | 0.840 | **0.903** |

Canonical result files:

- `holdout_results_dense.csv`
- `holdout_results_hybrid.csv`

Case-level comparison: **1 improved, 0 worse, 11 unchanged**.

The holdout must not be used for further tuning and then presented again as unseen evaluation.

## Why page-level metrics matter

The real corpus is one long manual, so document-level recall and document MRR are almost guaranteed to be 1.0 and are not informative. The useful metrics are:

- Page Recall@1
- Page Recall@3
- Page Recall@5
- Page Mean Reciprocal Rank (MRR)

For full methodology and interpretation cautions, see [`../docs/EVALUATION.md`](../docs/EVALUATION.md).
