# 90-second portfolio demo script

1. **Problem (10s)** — “Engineers often need to search long technical manuals during troubleshooting. This prototype explores source-grounded AI assistance rather than autonomous control.”
2. **Architecture (15s)** — Briefly show the hybrid pipeline: page-aware PDF chunks, embeddings + ChromaDB, BM25, reciprocal rank fusion and page diversification.
3. **Corpus (10s)** — With the local real-manual index loaded, show that the experiment used a 533-page PLC manual producing 1,129 indexed chunks. Do not redistribute the vendor PDF.
4. **Technical query (20s)** — Ask: `What rated voltage and voltage range are specified for a CPU 1212C DC/DC/DC?`
5. **Grounded answer (15s)** — Show the structured answer and document-supported checks or details.
6. **Evidence (10s)** — Open the Evidence tab and point out the document name, physical PDF page and retrieved passage. Describe the retrieval score as a ranking signal, not confidence.
7. **Evaluation (10s)** — Mention the frozen 12-question holdout result: hybrid retrieval reached 83.3% Page Recall@1, 100% Page Recall@3 and 0.903 Page MRR.

For a public demo without the third-party manual, use the bundled synthetic corpus and ask:

```text
What should be checked when controller communication times out?
```

Do not claim that the system diagnoses equipment, validates vendor procedures or controls a PLC. Describe it as an engineering-documentation retrieval prototype.
