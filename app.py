from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import Settings
from src.service import DocumentationAssistantService


ROOT = Path(__file__).parent
DEMO_DIR = ROOT / "demo_docs"

st.set_page_config(
    page_title="Engineering Documentation Assistant",
    page_icon="🧭",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container {max-width: 1180px; padding-top: 2rem;}
.hero {padding: 1.2rem 1.4rem; border: 1px solid #d9e2ec; border-radius: 14px; margin-bottom: 1rem;}
.hero h1 {margin: 0 0 .35rem 0; font-size: 2rem;}
.hero p {margin: 0; color: #52606d;}
.source-card {border: 1px solid #d9e2ec; border-radius: 10px; padding: .85rem 1rem; margin: .4rem 0;}
.small-muted {color: #7b8794; font-size: .9rem;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <h1>Engineering Documentation Assistant</h1>
  <p>Source-grounded retrieval and structured AI answers for technical PDF documentation.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.caption(
    "Portfolio prototype only. It retrieves information from supplied documents and does not "
    "control industrial equipment. Engineering decisions should be reviewed by qualified "
    "personnel."
)

settings = Settings.from_env()

with st.sidebar:
    st.header("System")
    st.write(f"**Generation:** `{settings.generation_model}`")
    st.write(f"**Embeddings:** `{settings.embedding_model}`")
    st.write("**Retrieval:** `Hybrid dense + BM25`")
    st.write(f"**Top-k:** `{settings.top_k}`")
    st.caption("Retrieval scores are relative ranking signals, not confidence probabilities.")
    st.divider()
    st.subheader("Index documents")
    uploaded = st.file_uploader(
        "Upload PDF manuals",
        type=["pdf"],
        accept_multiple_files=True,
    )
    use_demo = st.checkbox("Use bundled synthetic demo corpus", value=True)
    index_clicked = st.button(
        "Build / rebuild index",
        type="primary",
        use_container_width=True,
    )

if not settings.openai_api_key:
    st.error(
        "`OPENAI_API_KEY` is not configured. Copy `.env.example` to `.env`, add your API key, "
        "then restart the app."
    )
    st.stop()

try:
    service = DocumentationAssistantService(settings)
except Exception as exc:
    st.error(f"Could not initialise the application: {exc}")
    st.stop()

if index_clicked:
    docs: list[tuple[str, bytes]] = []
    if use_demo:
        docs.extend(
            (path.name, path.read_bytes())
            for path in sorted(DEMO_DIR.glob("*.pdf"))
        )
    docs.extend((file.name, file.getvalue()) for file in (uploaded or []))

    if not docs:
        st.warning("Choose the demo corpus or upload at least one PDF.")
    else:
        with st.spinner("Extracting, chunking, embedding and indexing documents..."):
            try:
                stats = service.index_documents(docs, reset=True)
                st.session_state["index_stats"] = stats
                st.success(
                    f"Indexed {stats['documents']} document(s), {stats['pages']} page(s), "
                    f"and {stats['chunks']} chunk(s)."
                )
            except Exception as exc:
                st.error(f"Indexing failed: {exc}")

indexed_count = service.store.count()
indexed_chunks = service.store.all_chunks() if indexed_count else []
indexed_documents = len({chunk.document for chunk in indexed_chunks})
indexed_pages = len({(chunk.document, chunk.page) for chunk in indexed_chunks})

metric_docs, metric_pages, metric_chunks = st.columns(3)
metric_docs.metric("Documents", indexed_documents)
metric_pages.metric("Physical pages", indexed_pages)
metric_chunks.metric("Indexed chunks", indexed_count)

st.info(
    "Answers are constrained to retrieved evidence. Source IDs are mapped back to "
    "document/page metadata by the application rather than trusted from free-form model text."
)

st.subheader("Ask the documentation")
question = st.text_input(
    "Technical question",
    placeholder="Example: What should be checked when controller communication times out?",
    label_visibility="collapsed",
)
ask_clicked = st.button("Search and answer", type="primary")

if ask_clicked:
    if service.store.count() == 0:
        st.warning("Build the document index first.")
    elif not question.strip():
        st.warning("Enter a technical question.")
    else:
        with st.spinner("Retrieving evidence and generating a grounded response..."):
            try:
                response, hits = service.ask(question)
            except Exception as exc:
                st.error(f"Request failed: {exc}")
            else:
                answer_tab, evidence_tab, trace_tab = st.tabs(
                    ["Answer", "Evidence", "Retrieval trace"]
                )

                with answer_tab:
                    if response.supported_by_documents:
                        st.success("Supported by retrieved documentation")
                    else:
                        st.warning("Insufficient support in retrieved documentation")

                    st.markdown("### Answer")
                    st.write(response.answer)

                    if response.recommended_checks:
                        st.markdown("### Document-supported checks")
                        for item in response.recommended_checks:
                            st.markdown(f"- {item}")

                    if response.caveats:
                        st.markdown("### Caveats")
                        for item in response.caveats:
                            st.markdown(f"- {item}")

                with evidence_tab:
                    selected = [
                        hit for hit in hits if hit.source_id in response.source_ids
                    ]

                    if not response.supported_by_documents:
                        st.info(
                            "No retrieved passage was cited as sufficient support for an answer. "
                            "Review the Retrieval trace tab to see the candidate passages the "
                            "system considered."
                        )
                    elif not selected:
                        st.warning(
                            "The response was marked as supported, but no valid source IDs were "
                            "returned. Review the retrieval trace before relying on the answer."
                        )
                    else:
                        for hit in selected:
                            st.markdown(
                                f"""
<div class="source-card">
  <strong>{hit.source_id} · {hit.document}</strong><br/>
  <span class="small-muted">Page {hit.page} · retrieval score {hit.score:.3f}</span>
</div>
""",
                                unsafe_allow_html=True,
                            )
                            with st.expander("Show retrieved passage"):
                                st.write(hit.text)

                with trace_tab:
                    st.caption(
                        "Retrieval score is a relative fused ranking signal within this query; "
                        "it is not a calibrated probability or confidence score."
                    )
                    trace = pd.DataFrame(
                        [
                            {
                                "source": hit.source_id,
                                "document": hit.document,
                                "page": hit.page,
                                "retrieval_score": round(hit.score, 4),
                            }
                            for hit in hits
                        ]
                    )
                    st.dataframe(trace, use_container_width=True, hide_index=True)
