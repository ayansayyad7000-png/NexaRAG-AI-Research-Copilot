from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from nexarag.config import settings
from nexarag.ingestion.document_loader import SUPPORTED_EXTENSIONS
from nexarag.llm.ollama_client import OllamaError, health_check
from nexarag.rag.engine import RAGEngine


st.set_page_config(
    page_title="NexaRAG AI Research Copilot",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 NexaRAG — AI Research Copilot")
st.caption(
    "Upload your documents and ask source-grounded questions using a local Ollama model."
)

if "engine" not in st.session_state:
    st.session_state.engine = RAGEngine()

if "messages" not in st.session_state:
    st.session_state.messages = []

engine: RAGEngine = st.session_state.engine

with st.sidebar:
    st.header("⚙️ System")

    if health_check():
        st.success("Ollama connected")
    else:
        st.error("Ollama not detected")

    st.code(
        f"Chat: {settings.chat_model}\n"
        f"Embeddings: {settings.embed_model}\n"
        f"Top K: {settings.top_k}",
        language="text",
    )

    st.header("📚 Knowledge Base")
    st.metric("Indexed chunks", len(engine.store.chunks))

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=[ext.lstrip(".") for ext in sorted(SUPPORTED_EXTENSIONS)],
        accept_multiple_files=True,
    )

    if st.button("Build Knowledge Base", type="primary", use_container_width=True):
        if not uploaded_files:
            st.warning("Upload at least one document first.")
        else:
            temp_paths = []
            try:
                with st.spinner("Reading, chunking and embedding documents..."):
                    for uploaded in uploaded_files:
                        suffix = Path(uploaded.name).suffix
                        temp = tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=suffix,
                        )
                        temp.write(uploaded.getbuffer())
                        temp.close()
                        temp_paths.append(Path(temp.name))

                    with tempfile.TemporaryDirectory() as td:
                        clean_paths = []
                        for uploaded, temp_path in zip(uploaded_files, temp_paths):
                            clean = Path(td) / Path(uploaded.name).name
                            clean.write_bytes(temp_path.read_bytes())
                            clean_paths.append(clean)

                        result = engine.ingest(clean_paths, reset=True)

                st.session_state.messages = []
                st.success(
                    f"Indexed {result['chunks']} chunks from {len(result['files'])} file(s)."
                )
                st.rerun()

            except (ValueError, OllamaError) as exc:
                st.error(str(exc))
            finally:
                for path in temp_paths:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass

    if st.button("Clear Knowledge Base", use_container_width=True):
        engine.clear()
        st.session_state.messages = []
        st.success("Knowledge base cleared.")
        st.rerun()

st.divider()

if not engine.store.chunks:
    st.info(
        "Start by uploading a PDF, DOCX, TXT or Markdown file in the sidebar, "
        "then click **Build Knowledge Base**."
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    location = source["source"]
                    if source["page"]:
                        location += f" — page {source['page']}"
                    st.markdown(
                        f"**[{source['id']}] {location}**  \n"
                        f"Similarity: `{source['score']}`"
                    )
                    st.caption(source["snippet"])

question = st.chat_input(
    "Ask a question about your indexed documents...",
    disabled=not bool(engine.store.chunks),
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching documents and generating answer..."):
                result = engine.ask(question)

            st.markdown(result["answer"])

            with st.expander("Sources"):
                for source in result["sources"]:
                    location = source["source"]
                    if source["page"]:
                        location += f" — page {source['page']}"
                    st.markdown(
                        f"**[{source['id']}] {location}**  \n"
                        f"Similarity: `{source['score']}`"
                    )
                    st.caption(source["snippet"])

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                }
            )

        except (ValueError, OllamaError) as exc:
            st.error(str(exc))
