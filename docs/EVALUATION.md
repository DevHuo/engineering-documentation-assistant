# Evaluation methodology and results

## Evaluation goal

The evaluation measures whether retrieval surfaces the **physical PDF pages** that contain enough evidence to answer labelled engineering-document questions. Generation quality is intentionally evaluated separately from retrieval quality.

The real-manual experiment uses a 533-page Siemens S7-1200 G2 system manual downloaded and indexed locally. The PDF itself is not redistributed by this repository. The indexed corpus produced 1,129 page-aware text chunks with the project defaults.

## Development trajectory

The first dense-only baseline showed that semantic retrieval worked well for broad natural-language questions but could under-rank exact engineering identifiers and specification-table queries. Failure analysis found examples such as:

- an exact `CPU 1212C DC/DC/DC` voltage query where the correct page ranked just outside Top-5;
- a PUT/GET instruction query where the exact section ranked below broad communication-overview pages;
- repeated terminology across neighbouring OPC UA and PROFINET sections.

The retriever was then extended with:

1. dense embedding retrieval;
2. a lightweight BM25 lexical index that preserves identifiers such as `S7-1200`, `DC/DC/DC` and `PUT/GET`;
3. English stopword filtering for lexical ranking;
4. reciprocal rank fusion (RRF);
5. page-level diversification so duplicate chunks from one page do not consume the whole Top-k window.

## Ground-truth adjudication

During development-set review, several questions had more than one page that independently contained enough evidence to answer the question. Treating only one of those pages as correct would understate retrieval quality. The labels were therefore adjudicated to allow multiple valid physical PDF pages where justified.

The initial label set is retained for traceability. The adjudicated real-manual set remains a **development set** because it was inspected during retrieval design.

## Metrics

The evaluator reports:

- document recall@k;
- page recall@1;
- page recall@3;
- page recall@k;
- document mean reciprocal rank (MRR);
- page MRR.

For a single-document corpus, the page-level metrics are the meaningful measures.

## Development-set results

The adjudicated development set contains 15 questions.

| Metric | Dense retrieval | Hybrid retrieval |
| --- | ---: | ---: |
| Page Recall@1 | 0.467 | **0.667** |
| Page Recall@3 | 0.867 | **0.933** |
| Page Recall@5 | **0.933** | **0.933** |
| Page MRR | 0.672 | **0.800** |

Case-level comparison showed **4 improved**, **1 worse** and **10 unchanged** under the hybrid retriever. These results are useful for development history but are not an unbiased final test because the questions informed retrieval design choices.

## Frozen holdout protocol

After the retrieval design was frozen, a separate 12-question holdout set was created from previously unused manual topics. Ground-truth physical PDF pages were recorded before retrieval was run. Retrieval parameters were not changed after the holdout results were inspected.

The holdout set includes topics such as CPU status LEDs, diagnostic-buffer security events, factory reset, load memory, trace recording, Secure Boot, NFC and DHCP configuration.

## Holdout results

| Metric | Dense retrieval | Hybrid retrieval |
| --- | ---: | ---: |
| Page Recall@1 | 0.750 | **0.833** |
| Page Recall@3 | 0.917 | **1.000** |
| Page Recall@5 | **1.000** | **1.000** |
| Page MRR | 0.840 | **0.903** |

On the 12 holdout questions, hybrid retrieval **improved 1 case, worsened 0 and left 11 unchanged**. Dense retrieval already achieved 100% Page Recall@5 on this set, so the hybrid design mainly improved the rank of answer-bearing pages rather than increasing Top-5 coverage.

## Interpretation cautions

- The holdout contains only 12 questions from one vendor manual; the results should not be generalized to all engineering documentation.
- Retrieval score in the UI is a ranking score, not a probability or confidence estimate.
- Exact page matching is strict; useful context can span adjacent pages.
- A higher retrieval metric does not prove that generated answers are technically correct or safe.
- Table-heavy pages and repeated model names can behave differently from prose-heavy troubleshooting sections.
- The holdout was not reused for tuning after results were observed.
- The project has not yet measured generation-level groundedness with an independent labelled answer set.

## Reproduce locally

The third-party manual is not included. After placing the matching PDF in `data/` and rebuilding the local index, run:

```bash
python scripts/evaluate_dense.py \
  --cases evaluation/real_questions.json \
  --top-k 5 \
  --output evaluation/real_results_dense_adjudicated.csv

python scripts/evaluate.py \
  --cases evaluation/real_questions.json \
  --top-k 5 \
  --output evaluation/real_results_hybrid_adjudicated.csv

python scripts/evaluate_dense.py \
  --cases evaluation/holdout_questions.json \
  --top-k 5 \
  --output evaluation/holdout_results_dense.csv

python scripts/evaluate.py \
  --cases evaluation/holdout_questions.json \
  --top-k 5 \
  --output evaluation/holdout_results_hybrid.csv
```

The checked-in CSV result files preserve the portfolio experiment outputs; re-running them requires the same locally supplied manual and current retrieval configuration.
