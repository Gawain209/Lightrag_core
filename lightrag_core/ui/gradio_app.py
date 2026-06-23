"""Gradio web UI for LightRAG-Core.

Thin UI layer on top of the FastAPI server — no duplication of RAG logic.
Run with: python -m lightrag_core.ui.gradio_app
"""

import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import gradio as gr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("lightrag_core.ui")

API_BASE = os.getenv("LIGHTRAG_API_BASE", "http://127.0.0.1:8000")
_client = httpx.Client(timeout=120)


def _api(path: str, method: str = "GET", **kwargs) -> dict[str, Any]:
    """Call the LightRAG-Core API and return parsed JSON."""
    url = f"{API_BASE}{path}"
    try:
        resp = _client.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot connect to LightRAG-Core API at {API_BASE}. "
            "Start the server first:\n"
            "  uvicorn lightrag_core.api.main:app --host 127.0.0.1 --port 8000"
        )
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:300]
        raise RuntimeError(f"API error {e.response.status_code}: {detail}")


# ── Knowledge Base helpers ──────────────────────────────────────────

def _get_kb_choices() -> list[tuple[str, str]]:
    """Return (name, id) pairs for all knowledge bases."""
    try:
        data = _api("/knowledge-bases")
        return [(kb["name"], kb["id"]) for kb in data.get("items", [])]
    except RuntimeError:
        return []


def _ensure_default_kb():
    """Ensure at least one knowledge base exists."""
    choices = _get_kb_choices()
    if not choices:
        try:
            _api("/knowledge-bases", method="POST", json={"name": "default"})
        except RuntimeError:
            pass
        return _get_kb_choices()
    return choices


# ── Chat function ───────────────────────────────────────────────────

def rag_chat(message: str, history: list, kb_id: str, top_k: int) -> str:
    """Process a chat message through the RAG pipeline.

    The `history` parameter is passed by ChatInterface but we don't use it —
    all context comes from vector search results.
    """
    if not kb_id:
        choices = _ensure_default_kb()
        if not choices:
            yield "Cannot create a knowledge base. Check that the API server is running."
            return
        kb_id = choices[0][1]

    try:
        data = _api("/query", method="POST", json={
            "kb_id": kb_id,
            "query": message,
            "top_k": top_k,
        })
    except RuntimeError as e:
        yield str(e)
        return

    answer = data["answer"]
    sources = data.get("sources", [])
    latency = data.get("latency_ms", 0)

    if sources:
        answer += f"\n\n---\n### Sources ({latency}ms)\n"
        for i, s in enumerate(sources):
            preview = s["content"][:200].replace("\n", " ")
            answer += f"\n**[{i+1}]** score={s['score']:.3f}  \n> {preview}..."

    yield answer


# ── Document upload ─────────────────────────────────────────────────

def upload_file(file_path: str | None, kb_id: str, title: str) -> str:
    """Upload a file to a knowledge base."""
    if file_path is None:
        return "No file selected."
    if not kb_id:
        return "Create a knowledge base first."

    path = Path(file_path)
    suffix = path.suffix.lower()

    # Formats that need parser-based extraction: upload via multipart to /documents/upload
    if suffix in (".pdf", ".docx", ".doc", ".html", ".htm", ".csv", ".json", ".xlsx"):
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".html": "text/html",
            ".htm": "text/html",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        try:
            with open(file_path, "rb") as f:
                resp = _client.post(
                    f"{API_BASE}/documents/upload",
                    files={"file": (path.name, f, mime_map.get(suffix, "application/octet-stream"))},
                    params={"kb_id": kb_id},
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError:
            return f"Cannot connect to API at {API_BASE}"
        except Exception as e:
            return f"Upload failed: {e}"
    else:
        try:
            content = path.read_text(encoding="utf-8")
            data = _api("/documents", method="POST", json={
                "kb_id": kb_id,
                "title": title or path.name,
                "content": content,
            })
        except RuntimeError as e:
            return str(e)
        except Exception as e:
            return f"Upload failed: {e}"

    return f"Uploaded: {data['title']} (id: {data['id'][:8]}...)"


def index_text(kb_id: str, content_text: str, title: str) -> str:
    """Index plain text into a knowledge base."""
    if not content_text.strip():
        return "Nothing to index."
    if not kb_id:
        return "Create a knowledge base first."

    title = title.strip() or f"text-{str(uuid.uuid4())[:6]}"
    try:
        data = _api("/documents", method="POST", json={
            "kb_id": kb_id,
            "title": title,
            "content": content_text,
        })
    except RuntimeError as e:
        return str(e)

    return f"Indexed: {data['title']} (id: {data['id'][:8]}...)"


def create_kb(name: str) -> tuple[str, gr.Dropdown]:
    """Create a new knowledge base."""
    if not name.strip():
        return "Enter a name.", gr.Dropdown()
    try:
        _api("/knowledge-bases", method="POST", json={"name": name.strip()})
    except RuntimeError as e:
        return str(e), gr.Dropdown()

    choices = _get_kb_choices()
    return f"Created '{name.strip()}'", gr.Dropdown(choices=choices)


# ── App builder ─────────────────────────────────────────────────────

def create_app() -> gr.Blocks:
    """Build the Gradio Blocks application."""

    css = """
    .chatbot { min-height: 500px !important; }
    footer { display: none !important; }
    """

    theme = gr.themes.Soft(
        primary_hue="slate",
        secondary_hue="slate",
    )

    with gr.Blocks(title="LightRAG-Core") as app:
        gr.Markdown(
            "# LightRAG-Core\n"
            "Lightweight RAG Framework — Web Interface\n\n"
            f"API: `{API_BASE}`"
        )

        # ── Sidebar: KB management & upload ──
        with gr.Row():
            with gr.Column(scale=1):
                kb_choices = _get_kb_choices()
                top_k_slider = gr.Slider(
                    minimum=1, maximum=50, value=20, step=1,
                    label="Max Results",
                )
                kb_dropdown = gr.Dropdown(
                    choices=kb_choices,
                    value=kb_choices[0][1] if kb_choices else None,
                    label="Knowledge Base",
                    interactive=True,
                )

                with gr.Accordion("New Knowledge Base", open=False):
                    kb_name = gr.Textbox(label="Name", placeholder="e.g. my-docs")
                    kb_btn = gr.Button("Create", variant="secondary", size="sm")
                    kb_msg = gr.Markdown("")

                with gr.Accordion("Upload File", open=False):
                    f_input = gr.File(
                        label="Select file",
                        file_types=[".txt", ".md", ".pdf", ".docx", ".doc", ".csv", ".json", ".html", ".htm", ".xlsx"],
                    )
                    f_title = gr.Textbox(label="Title (defaults to filename)")
                    f_msg = gr.Markdown("")

                with gr.Accordion("Paste Text", open=False):
                    t_input = gr.Textbox(
                        label="Content",
                        lines=8,
                        placeholder="Paste text to add to the knowledge base...",
                    )
                    t_title = gr.Textbox(label="Title (optional)")
                    t_btn = gr.Button("Add to KB", variant="primary", size="sm")
                    t_msg = gr.Markdown("")

            # ── Main: Chat ──
            with gr.Column(scale=2):
                chat = gr.ChatInterface(
                    fn=rag_chat,
                    chatbot=gr.Chatbot(height=520, label="Conversation"),
                    additional_inputs=[kb_dropdown, top_k_slider],
                    additional_inputs_accordion=None,
                    title=None,
                )

        # ── Events ──
        kb_btn.click(
            fn=create_kb,
            inputs=[kb_name],
            outputs=[kb_msg, kb_dropdown],
        )

        f_input.upload(
            fn=upload_file,
            inputs=[f_input, kb_dropdown, f_title],
            outputs=[f_msg],
        )

        t_btn.click(
            fn=index_text,
            inputs=[kb_dropdown, t_input, t_title],
            outputs=[t_msg],
        )

    return app


# ── Launcher ────────────────────────────────────────────────────────

def main():
    """Launch the Gradio UI with embedded API server."""
    import threading

    import uvicorn

    # Start FastAPI in a background daemon thread
    logger.info("Starting FastAPI server...")
    api_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": "lightrag_core.api.main:app",
            "host": "127.0.0.1",
            "port": 8000,
            "log_level": "warning",
        },
        daemon=True,
    )
    api_thread.start()
    time.sleep(1.5)  # give it time to start

    # Ensure a default KB exists
    _ensure_default_kb()

    # Launch Gradio UI
    logger.info("Starting Gradio UI...")
    demo = create_app()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
        css=".chatbot { min-height: 500px !important; } footer { display: none !important; }",
        theme=gr.themes.Soft(primary_hue="slate", secondary_hue="slate"),
    )


if __name__ == "__main__":
    main()
