"""FastAPI backend for the RAG chatbot (Phase 3A & 3B).

Exposes the RAG core over HTTP with real SSE token streaming, real
Stop that cancels the active generation down to the provider socket,
conversation management, document ingestion & vectorstore management,
and benchmark evaluation suite.

Security: no endpoint in this module returns an API key, token or any other
secret value. ``/api/status`` reports only *whether* credentials are present
(booleans) plus configured non-secret model/embedding names.
"""

import asyncio
import io
import json
import logging
import os
import shutil
import time
from typing import Dict, List, Optional

import pandas as pd
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

try:  # package-relative (imported as src.api.main)
    from ..config import CHROMA_PATH, DATA_PATH, EMBEDDING_MODEL_NAME, GROQ_MODEL_NAME, WEB_SEARCH_PROVIDER
    from ..data_loader import clear_cached_chroma, load_documents, split_documents
    from ..utils.file_utils import delete_data_files, force_delete_directory, safe_filename
    from ..utils.env_utils import create_env_template, check_env_vars
except ImportError:  # flat import (PYTHONPATH=src)
    from config import CHROMA_PATH, DATA_PATH, EMBEDDING_MODEL_NAME, GROQ_MODEL_NAME, WEB_SEARCH_PROVIDER
    from data_loader import clear_cached_chroma, load_documents, split_documents
    from utils.file_utils import delete_data_files, force_delete_directory, safe_filename
    from utils.env_utils import create_env_template, check_env_vars

try:
    from .engine import AVAILABLE_GROQ_MODELS, DEFAULT_MODEL, EngineError, clear_cache, get_async_graph
    from .registry import STATUS_COMPLETED, STATUS_FAILED, STATUS_STOPPED, registry
    from .storage import (
        append_message,
        create_conversation,
        delete_conversation,
        get_conversation,
        list_conversations,
        update_conversation,
    )
    from .streaming import GenerationRunner
    from .titles import schedule_title_generation
except ImportError:  # flat import
    from engine import AVAILABLE_GROQ_MODELS, DEFAULT_MODEL, EngineError, clear_cache, get_async_graph
    from registry import STATUS_COMPLETED, STATUS_FAILED, STATUS_STOPPED, registry
    from storage import (
        append_message,
        create_conversation,
        delete_conversation,
        get_conversation,
        list_conversations,
        update_conversation,
    )
    from streaming import GenerationRunner
    from titles import schedule_title_generation

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Knowra - Multi-Source RAG Chatbot API", version="1.0.0")

# Dev server origins allowed for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for latest evaluation results (for CSV export)
_latest_eval_results: Optional[pd.DataFrame] = None


# --- Schemas --------------------------------------------------------------

class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    conversation_id: str = Field(default="default", min_length=1)
    chat_history: List[dict] = Field(default_factory=list)
    forced_mode: Optional[str] = Field(default=None)
    model: Optional[str] = None
    selected_model: Optional[str] = None


class StopRequest(BaseModel):
    generation_id: Optional[str] = None


class CreateConversationRequest(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = "New Chat"


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[dict]] = None


class MessageItem(BaseModel):
    role: str
    content: str
    mode: Optional[str] = None
    time: Optional[str] = None
    sources: Optional[List[str]] = None
    stopped: Optional[bool] = False
    error: Optional[bool] = False


class EvalRunRequest(BaseModel):
    num_questions: int = Field(default=5, ge=1)
    model: Optional[str] = None


# --- Health & Status ------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "active_generations": registry.active_summary()}


@app.get("/api/models")
async def list_models():
    """Model catalogue for the UI selector. Contains no credentials."""
    return {"models": AVAILABLE_GROQ_MODELS, "default": DEFAULT_MODEL}


@app.get("/api/status")
async def status():
    """Configuration *availability* only -- never the secret values themselves."""
    vectorstore_exists = os.path.exists(CHROMA_PATH) and os.path.isdir(CHROMA_PATH)
    file_count = len([f for f in os.listdir(DATA_PATH) if os.path.isfile(os.path.join(DATA_PATH, f))]) if os.path.exists(DATA_PATH) else 0

    return {
        "configured": {
            "groq_api_key": bool(os.getenv("GROQ_API_KEY")),
            "tavily_api_key": bool(os.getenv("TAVILY_API_KEY")),
            "langchain_api_key": bool(os.getenv("LANGCHAIN_API_KEY")),
        },
        "model": os.getenv("GROQ_MODEL_NAME", GROQ_MODEL_NAME),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "web_search_provider": WEB_SEARCH_PROVIDER,
        "vectorstore_present": vectorstore_exists,
        "data_files_count": file_count,
        "active_generations": registry.active_summary(),
    }


# --- Chat & Streaming -----------------------------------------------------

@app.post("/api/chat")
async def chat(req: ChatRequest = Body(...)):
    """Stream a chat response over SSE.

    Event types: ``started``, ``retrieval``, ``sources``, ``token`` (repeated),
    then exactly one of ``completed`` / ``stopped`` / ``error``.
    """
    try:
        generation = registry.register(req.conversation_id)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Auto-persist user message
    try:
        conv = get_conversation(req.conversation_id)
        messages = conv.get("messages", []) if conv else []
        if not (messages and messages[-1].get("role") == "user" and messages[-1].get("content") == req.query):
            append_message(req.conversation_id, {
                "role": "user",
                "content": req.query,
                "time": time.strftime("%I:%M %p"),
            })
    except Exception as e:
        logger.warning("Could not auto-persist user message: %s", e)

    model_to_use = req.model or req.selected_model
    runner = GenerationRunner(
        generation=generation,
        query=req.query,
        chat_history=req.chat_history,
        forced_mode=req.forced_mode,
        model=model_to_use,
    )

    try:
        async def body():
            try:
                async for event in runner.events():
                    data_str = json.dumps(event["data"]) if not isinstance(event["data"], str) else event["data"]
                    yield {"event": event["event"], "data": data_str}
            finally:
                registry.release(generation.conversation_id, generation.generation_id)
                # Auto-persist assistant response and trigger topic title generation
                try:
                    res = runner.result()
                    status_res = res.get("status")
                    ans = res.get("answer") or ""
                    if status_res == STATUS_COMPLETED:
                        append_message(req.conversation_id, {
                            "role": "assistant",
                            "content": ans,
                            "time": time.strftime("%I:%M %p"),
                            "stopped": False,
                        })
                        schedule_title_generation(req.conversation_id, req.query, ans, model_to_use)
                    elif status_res == STATUS_STOPPED:
                        append_message(req.conversation_id, {
                            "role": "assistant",
                            "content": ans,
                            "time": time.strftime("%I:%M %p"),
                            "stopped": True,
                        })
                        schedule_title_generation(req.conversation_id, req.query, ans, model_to_use)
                    elif status_res == STATUS_FAILED:
                        append_message(req.conversation_id, {
                            "role": "assistant",
                            "content": str(res.get("error") or "Generation failed"),
                            "mode": "error",
                            "error": True,
                            "time": time.strftime("%I:%M %p"),
                            "stopped": False,
                        })
                except Exception as save_err:
                    logger.warning("Could not auto-persist assistant message: %s", save_err)

        return EventSourceResponse(body(), ping=15)
    except Exception:
        registry.finish(generation, STATUS_FAILED, error="failed to start stream")
        registry.release(generation.conversation_id, generation.generation_id)
        raise


@app.post("/api/chat/{conversation_id}/stop")
async def stop(conversation_id: str, req: StopRequest = Body(default=StopRequest())):
    """Cancel an in-flight generation with true socket abortion."""
    result = await registry.stop(conversation_id, req.generation_id)
    if not result.get("stopped") and result.get("reason") == "not_found":
        raise HTTPException(status_code=404, detail="No such generation for this conversation.")
    return result


@app.get("/api/chat/{conversation_id}/status")
async def generation_status(conversation_id: str):
    """Current state of a conversation's active generation."""
    active = registry.active_generation(conversation_id)
    if active is None:
        return {"conversation_id": conversation_id, "status": "idle", "generation_id": None}
    return {
        "conversation_id": conversation_id,
        "generation_id": active.generation_id,
        "status": active.status,
    }


# --- Conversations Management ---------------------------------------------

@app.get("/api/conversations")
async def get_conversations():
    """List all saved conversations."""
    return {"conversations": list_conversations()}


@app.post("/api/conversations")
async def new_conversation(req: CreateConversationRequest = Body(default=CreateConversationRequest())):
    """Create a new conversation session."""
    conv = create_conversation(conversation_id=req.id, title=req.title or "New Chat")
    return conv


@app.get("/api/conversations/{conversation_id}")
async def fetch_conversation(conversation_id: str):
    """Get full conversation details including messages."""
    conv = get_conversation(conversation_id)
    if not conv:
        # Create empty conversation for the requested ID if not found
        conv = create_conversation(conversation_id=conversation_id)
    return conv


@app.put("/api/conversations/{conversation_id}")
async def update_conv(conversation_id: str, req: UpdateConversationRequest = Body(...)):
    """Update conversation title or replace messages."""
    updated = update_conversation(conversation_id, title=req.title, messages=req.messages)
    return updated or {}


@app.delete("/api/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """Delete a conversation."""
    deleted = delete_conversation(conversation_id)
    return {"success": deleted, "conversation_id": conversation_id}


@app.post("/api/conversations/{conversation_id}/messages")
async def add_message(conversation_id: str, message: MessageItem = Body(...)):
    """Append a message to a conversation."""
    conv = append_message(conversation_id, message.model_dump())
    return conv


# --- Documents & Vectorstore Management -----------------------------------

@app.get("/api/documents")
async def list_documents():
    """List documents in the data folder and vectorstore status."""
    os.makedirs(DATA_PATH, exist_ok=True)
    files = []
    for entry in os.scandir(DATA_PATH):
        if entry.is_file():
            stat = entry.stat()
            files.append({
                "name": entry.name,
                "size_bytes": stat.st_size,
                "size_formatted": f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024*1024 else f"{stat.st_size / (1024*1024):.2f} MB",
                "modified_at": stat.st_mtime,
            })
    files.sort(key=lambda x: x["modified_at"], reverse=True)
    vs_exists = os.path.exists(CHROMA_PATH) and os.path.isdir(CHROMA_PATH)
    return {
        "files": files,
        "count": len(files),
        "vectorstore_exists": vs_exists,
        "chroma_path": CHROMA_PATH,
    }


@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload one or more PDF or TXT documents to ./data/."""
    os.makedirs(DATA_PATH, exist_ok=True)
    uploaded = []
    errors = []

    for file in files:
        if not file.filename:
            continue
        clean_name = safe_filename(file.filename)
        dest_path = os.path.join(DATA_PATH, clean_name)
        try:
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded.append(clean_name)
        except Exception as e:
            errors.append(f"{file.filename}: {e}")
        finally:
            await file.close()

    return {
        "uploaded": uploaded,
        "errors": errors,
        "total_uploaded": len(uploaded),
    }


@app.delete("/api/documents/delete-all")
async def delete_all_docs():
    """Delete all files in the data directory."""
    try:
        deleted, failed = delete_data_files(DATA_PATH)
        return {"deleted_count": deleted, "failed_files": failed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete data files: {e}")


@app.delete("/api/documents/{filename}")
async def delete_single_doc(filename: str):
    """Delete a single document from ./data/."""
    clean_name = safe_filename(filename)
    target = os.path.join(DATA_PATH, clean_name)
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        os.remove(target)
        return {"success": True, "deleted": clean_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")


@app.post("/api/vectorstore/rebuild")
async def rebuild_vs():
    """Rebuild ChromaDB from documents in ./data/."""
    if not os.path.exists(DATA_PATH) or not os.listdir(DATA_PATH):
        raise HTTPException(status_code=400, detail="No documents found in data folder to index.")

    try:
        # 1. Clear cached engines and cached vectorstore
        clear_cache()
        clear_cached_chroma()
        # 2. Delete existing vectorstore safely
        if os.path.exists(CHROMA_PATH):
            force_delete_directory(CHROMA_PATH)
        # 3. Load, split and ingest
        docs = load_documents(DATA_PATH)
        if not docs:
            raise HTTPException(status_code=400, detail="No readable text found in documents.")
        chunks = split_documents(docs)

        # 4. Ingest into Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import Chroma

        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
        )
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH,
        )
        return {
            "success": True,
            "docs": len(docs),
            "chunks": len(chunks),
            "message": f"Successfully indexed {len(docs)} documents into {len(chunks)} chunks.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error rebuilding vectorstore: %s", e)
        raise HTTPException(status_code=500, detail=f"Error rebuilding vectorstore: {e}")


@app.delete("/api/vectorstore/delete")
async def delete_vs():
    """Purge the persistent vectorstore."""
    try:
        clear_cache()
        clear_cached_chroma()
        if os.path.exists(CHROMA_PATH):
            force_delete_directory(CHROMA_PATH)
        return {"success": True, "message": "Vectorstore deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete vectorstore: {e}")


# --- Evaluation Suite -----------------------------------------------------

def _get_benchmark_csv_path() -> str:
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tests", "benchmark_questions.csv"),
        os.path.join(".", "tests", "benchmark_questions.csv"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


@app.get("/api/evaluate/questions")
async def get_evaluation_questions():
    """Fetch the default benchmark questions."""
    csv_path = _get_benchmark_csv_path()
    if not os.path.exists(csv_path):
        return {"questions": [], "count": 0}
    try:
        df = pd.read_csv(csv_path)
        questions = df.to_dict(orient="records")
        return {"questions": questions, "count": len(questions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read benchmark questions: {e}")


@app.post("/api/evaluate/run")
async def run_evaluation_suite(req: EvalRunRequest = Body(...)):
    """Run evaluation against benchmark questions."""
    global _latest_eval_results

    csv_path = _get_benchmark_csv_path()
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Benchmark questions CSV not found.")

    try:
        benchmark_df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {e}")

    num_q = min(req.num_questions, len(benchmark_df))
    selected_model = req.model or os.getenv("GROQ_MODEL_NAME", DEFAULT_MODEL)

    results = []
    subset = benchmark_df.head(num_q)

    # Use async graph for evaluation
    graph = get_async_graph(selected_model)

    for index, row in subset.iterrows():
        question_id = row.get("question_id", index + 1)
        question = row["question"]
        expected_mode = str(row.get("expected_mode", "N/A")).strip().lower()

        start_time = time.time()
        answer = ""
        actual_mode = "unknown"
        error_msg = None
        sources_used = None

        try:
            # Run graph directly
            final_state = await graph.ainvoke({
                "query": question,
                "chat_history": [],
            })
            answer = final_state.get("answer", "No answer found")
            actual_mode = str(final_state.get("retrieval_mode", "unknown")).strip().lower()
            error_msg = final_state.get("error")

            docs = final_state.get("documents", [])
            if docs:
                sources = []
                for d in docs:
                    if isinstance(d, str):
                        for line in d.splitlines():
                            if line.startswith("Source URL:"):
                                url = line.split("Source URL:", 1)[1].strip()
                                if url and url != "N/A" and url not in sources:
                                    sources.append(url)
                if sources:
                    sources_used = ", ".join(sources)
                elif final_state.get("generation_source") == "vectorstore":
                    sources_used = "Chroma Vectorstore"

            if error_msg:
                actual_mode = "error"
        except Exception as e:
            answer = f"Error: {e}"
            actual_mode = "error"
            error_msg = str(e)

        latency = time.time() - start_time
        mode_correct = None
        if expected_mode != "n/a" and actual_mode != "error":
            mode_correct = (expected_mode == actual_mode)

        results.append({
            "question_id": question_id,
            "question": question,
            "expected_mode": expected_mode if expected_mode != "n/a" else None,
            "actual_mode": actual_mode,
            "mode_correct": mode_correct,
            "answer": answer,
            "latency_seconds": round(latency, 3),
            "sources_used": sources_used,
            "error": error_msg,
        })

    results_df = pd.DataFrame(results)
    _latest_eval_results = results_df

    # Calculate summary metrics
    total_q = len(results)
    successful = len([r for r in results if not r.get("error")])
    error_rate = ((total_q - successful) / total_q) * 100 if total_q > 0 else 0
    evaluable = [r for r in results if r.get("expected_mode") is not None and r.get("mode_correct") is not None]
    mode_accuracy = (sum(1 for r in evaluable if r["mode_correct"]) / len(evaluable)) * 100 if evaluable else 0
    avg_latency = sum(r["latency_seconds"] for r in results) / total_q if total_q > 0 else 0

    return {
        "summary": {
            "total_questions": total_q,
            "successful_runs": successful,
            "error_rate_pct": round(error_rate, 1),
            "mode_accuracy_pct": round(mode_accuracy, 1),
            "avg_latency_seconds": round(avg_latency, 2),
            "model_used": selected_model,
        },
        "results": results,
    }


@app.get("/api/evaluate/export")
async def export_evaluation_results():
    """Download the latest evaluation results as CSV."""
    global _latest_eval_results
    if _latest_eval_results is None or _latest_eval_results.empty:
        raise HTTPException(status_code=404, detail="No evaluation results available for export.")

    stream = io.StringIO()
    _latest_eval_results.to_csv(stream, index=False)
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="evaluation_results.csv"'},
    )
    return response


# --- Environment Template -------------------------------------------------

@app.get("/api/env/template")
async def get_env_template():
    """Return a safe template for .env configuration."""
    template = create_env_template()
    return PlainTextResponse(template)


# --- Static Frontend Serving (if built) -----------------------------------

frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if not os.path.exists(frontend_dist):
    frontend_dist = os.path.abspath(os.path.join(".", "frontend", "dist"))

if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path == "openapi.json":
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return PlainTextResponse("Multi-Source RAG Chatbot API. See /docs.")
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return PlainTextResponse("Multi-Source RAG Chatbot API. See /docs.")
