from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.config import settings
from src.document_loader import SUPPORTED_EXTENSIONS
from src.ollama_client import OllamaError, health_check
from src.rag import RAGEngine


st.set_page_config(page_title="NexaRAG AI Research Copilot", page_icon="🧠", layout="wide")
st.title("🧠 NexaRAG — AI Research Copilot")
st.caption("Upload your documents and ask source-grounded questions using a local Ollama model.")

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
        f"Chat: {settings.chat_model}\nEmbeddings: {settings.embed_model}\nTop K: {settings.top_k}",
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
            try:
                with tempfile.TemporaryDirectory() as td:
                    paths = []
                    for uploaded in uploaded_files:
                        path = Path(td) / Path(uploaded.name).name
                        path.write_bytes(uploaded.getbuffer())
                        paths.append(path)
                    with st.spinner("Reading, chunking and embedding documents..."):
                        result = engine.ingest(paths, reset=True)
                st.session_state.messages = []
                st.success(f"Indexed {result['chunks']} chunks from {len(result['files'])} file(s).")
                st.rerun()
            except (ValueError, OllamaError) as exc:
                st.error(str(exc))

    if st.button("Clear Knowledge Base", use_container_width=True):
        engine.clear()
        st.session_state.messages = []
        st.success("Knowledge base cleared.")
        st.rerun()

st.divider()

if not engine.store.chunks:
    st.info("Start by uploading a PDF, DOCX, TXT or Markdown file in the sidebar, then click **Build Knowledge Base**.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    location = source["source"]
                    if source["page"]:
                        location += f" — page {source['page']}"
                    st.markdown(f"**[{source['id']}] {location}**  \nSimilarity: `{source['score']}`")
                    st.caption(source["snippet"])

question = st.chat_input("Ask a question about your indexed documents...", disabled=not bool(engine.store.chunks))

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
                    st.markdown(f"**[{source['id']}] {location}**  \nSimilarity: `{source['score']}`")
                    st.caption(source["snippet"])
            st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"]})
        except (ValueError, OllamaError) as exc:
            st.error(str(exc))
