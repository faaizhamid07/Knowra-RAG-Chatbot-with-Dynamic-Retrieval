"""Engine construction: builds and caches the async RAG graph per model."""

import logging
import os
import threading
from typing import Dict, Optional

from langchain_groq import ChatGroq

try:  # package-relative (imported as src.api.engine)
    from ..chatbot_graph_async import build_chatbot_graph_async
except ImportError:  # flat import (PYTHONPATH=src)
    from chatbot_graph_async import build_chatbot_graph_async

logger = logging.getLogger(__name__)

# Mirrors the model list offered by the model selector.
AVAILABLE_GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "allam-2-7b",
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-qwen-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]

DEFAULT_MODEL = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")

_cache: Dict[str, object] = {}
_lock = threading.Lock()


class EngineError(RuntimeError):
    """Raised when the graph cannot be constructed (e.g. missing API key)."""


def get_async_graph(model: str = DEFAULT_MODEL):
    """Return a compiled async graph for ``model``, building it on first use.

    ``build_chatbot_graph_async`` assigns a module-level LLM handle, so graphs
    for different models cannot be trusted concurrently. Rather than ship that
    hazard, one model is live at a time and switching models invalidates the
    cache. Recorded as a Phase 3A limitation; the fix is per-graph LLM
    injection (drop the module global), which is a change to the shared
    prompt/routing module and so was left out of this phase.
    """
    with _lock:
        cached = _cache.get(model)
        if cached is not None:
            return cached

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EngineError("GROQ_API_KEY is not configured on the server.")

        llm_instance = ChatGroq(
            temperature=0,
            groq_api_key=api_key,
            model_name=model,
        )
        graph = build_chatbot_graph_async(llm_instance=llm_instance)
        _cache.clear()  # only one model live at a time (see docstring)
        _cache[model] = graph
        return graph


def clear_cache() -> None:
    with _lock:
        _cache.clear()