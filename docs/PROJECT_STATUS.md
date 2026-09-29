# Project status

## Current state

The core portfolio project is complete and the retrieval design is frozen. Remaining work is presentation-oriented: final local UI verification, screenshots, GitHub publication and CV/application wording.

## Completed

- Source-grounded RAG pipeline over technical PDFs
- Page-aware PDF extraction and chunking
- OpenAI embeddings + ChromaDB persistence
- Hybrid dense + BM25 retrieval
- Stopword-aware technical tokenisation
- Reciprocal rank fusion
- Page-level diversification
- Structured Pydantic answer output
- Streamlit evidence and retrieval-trace UI
- Explicit unsupported-query behaviour
- Synthetic reproducible evaluation set
- 15-question real-manual development evaluation set
- Ground-truth adjudication with multi-positive pages where justified
- Dense-only and hybrid evaluation scripts
- Case-level evaluation comparison script
- Frozen 12-question holdout set
- Independent holdout evaluation after retrieval freeze
- Unit tests for retrieval, page diversification, multi-positive labels, chunking and vector search
- GitHub Actions CI configuration

## Development-set results

| Metric | Dense | Hybrid |
| --- | ---: | ---: |
| Page Recall@1 | 0.467 | **0.667** |
| Page Recall@3 | 0.867 | **0.933** |
| Page Recall@5 | **0.933** | **0.933** |
| Page MRR | 0.672 | **0.800** |

Development case comparison: **4 improved, 1 worse, 10 unchanged**.

## Frozen holdout results

| Metric | Dense | Hybrid |
| --- | ---: | ---: |
| Page Recall@1 | 0.750 | **0.833** |
| Page Recall@3 | 0.917 | **1.000** |
| Page Recall@5 | **1.000** | **1.000** |
| Page MRR | 0.840 | **0.903** |

Holdout case comparison: **1 improved, 0 worse, 11 unchanged**.

## Important evaluation boundary

Do not tune the current retrieval implementation against `evaluation/holdout_questions.json`. The holdout has already been observed and is now a reporting artifact rather than a development set.

## Final publication checklist

1. Run the eight unit tests locally.
2. Launch Streamlit against the local real-manual index and verify supported and unsupported queries.
3. Capture two or three clean screenshots for the README or portfolio.
4. Confirm `.env`, `.chroma/`, `.venv/`, vendor PDFs and macOS metadata are not staged by Git.
5. Publish the repository without an open-source licence unless the author later chooses one deliberately.
6. Add the project to the Facteon-targeted CV using only metrics reproduced locally.
