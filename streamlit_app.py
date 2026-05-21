# streamlit_app.py

"""
Polyglot Document Workflow — Steps 1–3 Testing UI

Run with:
    streamlit run streamlit_app.py

Requires the FastAPI server to be running on localhost:8000.
"""

from __future__ import annotations

import httpx
import streamlit as st

API_BASE = "http://localhost:8000"
TIMEOUT  = httpx.Timeout(60.0)   # First search call loads the embedding model


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Polyglot Document Workflow",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Polyglot Document Workflow")
st.caption("Steps 1–3: Ingest → Chunk & Embed → Semantic Search")

# Initialise session state keys so the rest of the script can reference them safely
if "doc_id"     not in st.session_state: st.session_state.doc_id     = None
if "filename"   not in st.session_state: st.session_state.filename   = None
if "chunk_done" not in st.session_state: st.session_state.chunk_done = False


# ── Helper ────────────────────────────────────────────────────────────────────

def api_post(path: str, **kwargs) -> dict | None:
    """POST to the FastAPI server; display an error banner on failure."""
    try:
        r = httpx.post(f"{API_BASE}{path}", timeout=TIMEOUT, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text}")
    except httpx.ConnectError:
        st.error(
            "Could not connect to the API at `localhost:8000`. "
            "Is `uvicorn app.main:app --reload` running?"
        )
    return None


# ── Section 1 — Ingest ────────────────────────────────────────────────────────

st.header("① Ingest a Document")

uploaded = st.file_uploader(
    "Upload a PDF, DOCX, or plain-text file",
    type=["pdf", "docx", "txt"],
)

col1, col2 = st.columns([2, 3])

with col1:
    ingest_btn = st.button(
        "Ingest document",
        disabled=uploaded is None,
        use_container_width=True,
    )

if ingest_btn and uploaded:
    with st.spinner("Ingesting…"):
        result = api_post(
            "/documents/ingest",
            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
        )

    if result:
        st.session_state.doc_id     = result["doc_id"]
        st.session_state.filename   = result["filename"]
        st.session_state.chunk_done = False   # Reset if re-ingesting

        badge = "🟢 new" if result["status"] == "ready" else "🔵 duplicate"
        st.success(f"**Status:** {badge}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Document ID", result["doc_id"][:8] + "…")
        #c2.metric("Characters", f"{result.get('char_count', 0):,}")
        c2.metric("Characters", result['char_count'] if result['char_count'] is not None else "None") 
        c3.metric("MIME type", result["mime_type"].split("/")[-1].upper())
        
        


# ── Section 2 — Chunk & Embed ─────────────────────────────────────────────────

st.divider()
st.header("② Chunk & Embed")

doc_ready = st.session_state.doc_id is not None

if not doc_ready:
    st.info("Ingest a document first to enable this section.")

with st.form("chunk_form"):
    col_a, col_b, col_c = st.columns(3)

    strategy = col_a.selectbox(
        "Chunking strategy",
        ["fixed", "sentence_window", "recursive"],
        disabled=not doc_ready,
    )
    chunk_size = col_b.slider(
        "Chunk size (chars)",
        min_value=100, max_value=2000, value=500, step=100,
        disabled=not doc_ready,
    )
    overlap = col_c.slider(
        "Overlap (chars)",
        min_value=0, max_value=400, value=50, step=25,
        disabled=not doc_ready,
    )

    run_chunk = st.form_submit_button(
        "Chunk → Embed → Index",
        disabled=not doc_ready,
        use_container_width=True,
    )

if run_chunk and doc_ready:
    doc_id = st.session_state.doc_id

    with st.spinner("Chunking and embedding (may take a few seconds on first run)…"):
        chunk_result = api_post(
            f"/documents/{doc_id}/chunks",
            json={"strategy": strategy, "chunk_size": chunk_size, "chunk_overlap": overlap},
        )

    if chunk_result:
        with st.spinner("Upserting into vector store…"):
            upsert_result = api_post(
                "/chunks/upsert",
                json={"doc_id": doc_id, "strategy": strategy},
            )

        if upsert_result:
            st.session_state.chunk_done = True
            col_x, col_y = st.columns(2)
            col_x.metric("Chunks created", chunk_result.get("chunk_count", 0))
            col_y.metric("Vectors indexed", upsert_result.get("chunks_upserted", 0))
            st.success("Ready to search! ↓")


# ── Section 3 — Search ────────────────────────────────────────────────────────

st.divider()
st.header("③ Semantic Search")

search_ready = st.session_state.chunk_done

if not search_ready:
    st.info("Complete the Chunk & Embed step first to enable search.")

query_text = st.text_input(
    "Ask a question about your document",
    placeholder="e.g. What are the main conclusions?",
    disabled=not search_ready,
)

col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
top_k     = col_s2.slider("Top K results", 1, 20, 5, disabled=not search_ready)
min_score = col_s3.slider("Min score", 0.0, 1.0, 0.0, step=0.05, disabled=not search_ready)

scope     = col_s1.checkbox(
    "Restrict search to current document only",
    value=True,
    disabled=not search_ready,
)

search_btn = st.button(
    "Search",
    disabled=(not search_ready or not query_text),
    use_container_width=False,
    type="primary",
)

if search_btn and query_text:
    payload: dict = {
        "query": query_text,
        "top_k": top_k,
        "filters": {
            "min_score": min_score,
            "doc_ids": [st.session_state.doc_id] if scope else None,
        },
    }

    with st.spinner("Searching… (first query loads the embedding model — ~10s)"):
        result = api_post("/chunks/search", json=payload)

    if result:
        count = result["result_count"]
        ms    = result["query_embedding_ms"]

        st.caption(f"Found **{count}** result(s) · Query embedded in **{ms:.1f} ms**")

        if count == 0:
            st.warning(
                "No results above the score threshold. "
                "Try lowering Min score or rephrasing your question."
            )
        else:
            for i, res in enumerate(result["results"], start=1):
                score_pct = int(res["score"] * 100)

                # Colour the score badge: green ≥70, amber ≥40, red <40
                if score_pct >= 70:
                    badge_color = "green"
                elif score_pct >= 40:
                    badge_color = "orange"
                else:
                    badge_color = "red"

                with st.expander(
                    f"**#{i}** · :{badge_color}[{score_pct}% match] · "
                    f"`{res['filename']}` · chunk {res['chunk_index']}",
                    expanded=(i == 1),   # auto-expand the top result
                ):
                    st.markdown(res["text"])
                    st.caption(
                        f"chunk_id: `{res['chunk_id']}` · "
                        f"char_offset: {res['char_offset']:,} · "
                        f"doc_id: `{res['doc_id']}`"
                    )


# ── Sidebar — state inspector ─────────────────────────────────────────────────

with st.sidebar:
    st.subheader("Session state")
    st.json({
        "doc_id":     st.session_state.doc_id,
        "filename":   st.session_state.filename,
        "chunk_done": st.session_state.chunk_done,
    })

    st.divider()
    st.subheader("API endpoints")
    st.markdown(
        "- [Swagger UI](http://localhost:8000/docs)\n"
        "- [Redoc](http://localhost:8000/redoc)\n"
        "- [Health](http://localhost:8000/health)"
    )

    if st.button("Reset session", use_container_width=True):
        for key in ["doc_id", "filename", "chunk_done"]:
            del st.session_state[key]
        st.rerun()