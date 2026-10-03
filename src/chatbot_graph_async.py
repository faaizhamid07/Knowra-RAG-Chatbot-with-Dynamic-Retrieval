"""Async execution layer for the RAG graph.

This module is the streaming/cancellable twin of ``chatbot_graph``. It reuses
every prompt, routing rule and edge decision from the sync graph so the RAG
behaviour is preserved exactly, but expresses the nodes as coroutines so that:

* generation tokens are produced by a real provider stream (not a typewriter
  replay of a finished string), and
* cancelling the asyncio task that drives the graph raises
  ``asyncio.CancelledError`` *inside* the running node -- which, for the
  generation nodes, unwinds ``ChatGroq._astream`` and aborts the upstream
  ``httpx`` request to Groq.

The sync graph in ``chatbot_graph`` is left untouched and remains the engine
for the Streamlit app.

Design note on deltas: ``graph.astream_events`` is deliberately NOT used to
harvest tokens. It funnels the run through a log-tracer tee, and cancelling
its consumer does not reach the node (verified: the node runs to completion).
``graph.astream(stream_mode="updates")`` does propagate cancellation. So nodes
push deltas onto a queue that the HTTP layer drains, and ``astream`` is used
purely as the driver that keeps cancellation wired to the running node.
"""

import asyncio
import contextvars
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, StateGraph

try:  # package-relative (imported as src.chatbot_graph_async)
    from .chatbot_graph import (
        ChatbotState,
        CONDENSE_QUESTION_PROMPT,
        COMPREHENSIVE_ROUTER_PROMPT,
        VECTORSTORE_RAG_PROMPT,
        WEB_SEARCH_RAG_PROMPT,
        format_chat_history_for_prompt,
        decide_after_router,
        decide_after_vectorstore_retrieval,
        decide_after_web_retrieval,
        route_or_generate,
    )
    from .config import WEB_SEARCH_PROVIDER
    from .data_loader import get_vectorstore_retriever
    from .tools import get_web_search_tool
except ImportError:  # flat import (PYTHONPATH=src)
    from chatbot_graph import (
        ChatbotState,
        CONDENSE_QUESTION_PROMPT,
        COMPREHENSIVE_ROUTER_PROMPT,
        VECTORSTORE_RAG_PROMPT,
        WEB_SEARCH_RAG_PROMPT,
        format_chat_history_for_prompt,
        decide_after_router,
        decide_after_vectorstore_retrieval,
        decide_after_web_retrieval,
        route_or_generate,
    )
    from config import WEB_SEARCH_PROVIDER
    from data_loader import get_vectorstore_retriever
    from tools import get_web_search_tool

logger = logging.getLogger(__name__)

# --- Delta bridge ---------------------------------------------------------
# ContextVars propagate into the asyncio tasks LangGraph spawns for nodes
# (verified), which is how a node reaches the SSE queue without the graph
# having to know anything about HTTP.
_DELTA_SINK: "contextvars.ContextVar[Optional[Callable[[str], None]]]" = contextvars.ContextVar(
    "rag_delta_sink", default=None
)


def set_delta_sink(sink: Optional[Callable[[str], None]]):
    """Bind a token sink for the current async context. Returns a reset token."""
    return _DELTA_SINK.set(sink)


def reset_delta_sink(token) -> None:
    if token is not None:
        _DELTA_SINK.reset(token)


def emit_delta(text: str) -> None:
    """Push a token delta to the active sink, if one is bound."""
    if not text:
        return
    sink = _DELTA_SINK.get()
    if sink is not None:
        sink(text)


# --- LLM handle -----------------------------------------------------------
# Module-local so the async graph never mutates the sync graph's global.
llm = None


def _require_llm():
    if llm is None:
        raise RuntimeError("Async chatbot graph used before build_chatbot_graph_async()")
    return llm


# --- Async nodes ----------------------------------------------------------

async def route_query_node(state: ChatbotState) -> Dict[str, Any]:
    """Async twin of ``chatbot_graph.route_query_node`` (identical decisions)."""
    logger.info("--- Routing Query (Comprehensive LLM Router, async) ---")
    query = state["query"]
    chat_history_str = format_chat_history_for_prompt(state["chat_history"])
    try:
        router_chain = COMPREHENSIVE_ROUTER_PROMPT | _require_llm()
        response = await router_chain.ainvoke({"query": query, "chat_history": chat_history_str})
        decision = response.content.strip().lower()
        logger.info(f"Initial comprehensive routing decision: {decision}")

        # Keyword overrides -- identical to the sync node.
        if re.search(r"\b(latest|current|news|today|update)\b", query, re.IGNORECASE):
            logger.info("Overriding decision to 'web_search' based on query indicating current events or updates.")
            decision = "web_search"
        elif re.search(
            r"\b(transformer|rag|attention|fine[- ]?tuning|vector search|mixtral|bert|explain|how does|paper|model|algorithm)\b",
            query,
            re.IGNORECASE,
        ):
            logger.info("Overriding decision to 'vectorstore' based on AI topic keywords in query.")
            decision = "vectorstore"

        if "llm_native" in decision:
            final_decision = "llm_native"
        elif "vectorstore" in decision:
            final_decision = "vectorstore"
        elif "web_search" in decision:
            final_decision = "web_search"
        else:
            logger.warning(f"Comprehensive Router unexpected decision: '{decision}'. Defaulting to vectorstore.")
            final_decision = "vectorstore"

        logger.info(f"Final routing decision: {final_decision}")
        return {"retrieval_mode": final_decision}
    except asyncio.CancelledError:
        raise  # never swallow cancellation
    except Exception as e:
        logger.error(f"Error during comprehensive routing: {e}", exc_info=True)
        return {"retrieval_mode": "vectorstore", "error": f"Failed comprehensive routing, trying VS: {e}"}


async def get_standalone_query(state: ChatbotState) -> str:
    """Async twin of ``chatbot_graph.get_standalone_query``."""
    chat_history = state.get("chat_history", [])
    query = state["query"]
    if not chat_history:
        return query

    chat_history_str = format_chat_history_for_prompt(chat_history)
    try:
        condense_chain = CONDENSE_QUESTION_PROMPT | _require_llm()
        response = await condense_chain.ainvoke({"chat_history": chat_history_str, "question": query})
        standalone_query = response.content.strip()
        logger.info(f"Original Query: '{query}' -> Standalone Query: '{standalone_query}'")
        return standalone_query
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error condensing query: {e}. Falling back to original query.", exc_info=True)
        return query


async def retrieve_vectorstore_node(state: ChatbotState) -> Dict[str, Any]:
    """Async twin of ``chatbot_graph.retrieve_vectorstore_node``.

    Chroma runs locally on CPU with no I/O to abort, so the blocking search is
    pushed to a worker thread via ``asyncio.to_thread``. The loop stays
    responsive (so a Stop request is still accepted) but the in-flight search
    itself cannot be interrupted -- documented as a Phase 3A limitation.
    """
    logger.info("--- Retrieving from Vectorstore ---")
    query = state["query"]
    standalone_query = await get_standalone_query(state)
    try:
        retriever = await asyncio.to_thread(get_vectorstore_retriever, 7)
        documents = await asyncio.to_thread(retriever.invoke, standalone_query)
        doc_contents = [doc.page_content for doc in documents]
        logger.info(f"Retrieved {len(doc_contents)} chunks from vectorstore.")
        if doc_contents:
            logger.debug(f"First retrieved doc snippet: {doc_contents[0][:200]}...")
        return {"documents": doc_contents, "generation_source": "vectorstore", "retrieval_mode": "vectorstore"}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error during vectorstore retrieval: {e}", exc_info=True)
        return {"documents": [], "retrieval_mode": "vectorstore", "error": f"Vectorstore retrieval failed: {e}"}


async def retrieve_web_node(state: ChatbotState) -> Dict[str, Any]:
    """Async twin of ``chatbot_graph.retrieve_web_node``.

    Uses the tool's ``arun`` so the Tavily request is a cancellable httpx
    call rather than a blocking sync invoke.
    """
    logger.info("--- Retrieving from Web Search ---")
    standalone_query = await get_standalone_query(state)
    current_mode = state["retrieval_mode"]  # Should be 'web_search'
    try:
        search_tool = get_web_search_tool(max_results=4)
        if WEB_SEARCH_PROVIDER == "tavily":
            results = await search_tool.arun({"query": standalone_query})
            if isinstance(results, list) and results:
                results_str = "\n\n".join(
                    f"Source URL: {res.get('url', 'N/A')}\nContent: {res.get('content', 'N/A')}"
                    for res in results
                    if res.get("content")
                )
            elif isinstance(results, str):
                results_str = results
            else:
                results_str = ""
        else:
            raise NotImplementedError(f"Web provider {WEB_SEARCH_PROVIDER} not implemented.")

        retrieved_docs = [results_str] if results_str else []
        if retrieved_docs:
            logger.info(f"Retrieved web search results (length: {len(results_str)}).")
            return {"documents": retrieved_docs, "generation_source": "web_search", "retrieval_mode": current_mode}
        else:
            logger.warning("Web search returned no results. Setting mode for fallback.")
            return {"documents": [], "retrieval_mode": "llm_native"}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error during web search retrieval: {e}", exc_info=True)
        return {"documents": [], "retrieval_mode": "llm_native", "error": f"Web search failed: {e}"}


async def _stream_llm(runnable, input_value) -> str:
    """Consume a real provider stream, emitting each delta as it arrives.

    This is the single point where Stop becomes a provider-level abort: the
    ``async for`` is suspended inside ``ChatGroq._astream`` while it awaits
    the next chunk off the Groq HTTP response, so a ``CancelledError`` raised
    here unwinds that await and closes the response.
    """
    pieces: List[str] = []
    async for chunk in runnable.astream(input_value):
        text = chunk.content if isinstance(chunk, BaseMessage) else str(chunk)
        if text:
            pieces.append(text)
            emit_delta(text)
    return "".join(pieces)


async def generate_answer_rag_node(state: ChatbotState) -> Dict[str, Any]:
    """Async twin of ``generate_answer_rag_node`` that streams tokens."""
    source = state.get("generation_source")
    if not source:
        error_msg = "RAG generation called without a valid source (vectorstore/web_search)."
        logger.error(error_msg)
        return {"answer": f"Internal Error: {error_msg}", "retrieval_mode": "error", "error": error_msg}

    mode = source
    prompt_template = VECTORSTORE_RAG_PROMPT if mode == "vectorstore" else WEB_SEARCH_RAG_PROMPT
    logger.info(f"--- Generating RAG Answer (Source: {source}, streaming) ---")
    query = state["query"]
    documents = state["documents"]
    chat_history_str = format_chat_history_for_prompt(state["chat_history"])

    if not documents:
        logger.error(f"generate_answer_rag_node called with empty documents (Source: {source}).")
        return {
            "answer": "Internal Error: RAG generation called with no documents.",
            "retrieval_mode": "error",
            "error": f"RAG generation ({source}) called with no documents",
        }

    context = "\n\n".join(documents)
    logger.debug(f"Context length for LLM: {len(context)}")
    try:
        chain = prompt_template | _require_llm()
        answer = await _stream_llm(
            chain, {"context": context, "chat_history": chat_history_str, "question": query}
        )
        logger.info("LLM RAG generation complete.")
        return {"answer": answer, "retrieval_mode": mode}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error during RAG answer generation (Source: {source}): {e}", exc_info=True)
        return {
            "answer": f"Sorry, error generating {source} RAG answer.",
            "retrieval_mode": "error",
            "error": f"{source.capitalize()} RAG generation failed: {e}",
        }


async def generate_llm_native_node(state: ChatbotState) -> Dict[str, Any]:
    """Async twin of ``generate_llm_native_node`` that streams tokens."""
    logger.info("--- Generating Native LLM Answer (streaming) ---")
    query = state["query"]
    chat_history = state["chat_history"]
    history_messages: List[BaseMessage] = []
    for msg in chat_history[-6:]:
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history_messages.append(AIMessage(content=msg["content"]))

    native_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful AI assistant..."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{query}"),
        ]
    )
    try:
        chain = native_prompt | _require_llm()
        answer = await _stream_llm(chain, {"chat_history": history_messages, "query": query})
        logger.info("LLM native generation complete.")
        return {"answer": answer, "documents": [], "retrieval_mode": "llm_native"}
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Error during native LLM generation: {e}", exc_info=True)
        return {
            "answer": "Sorry, error generating native answer.",
            "retrieval_mode": "error",
            "error": f"Native generation failed: {e}",
        }


async def handle_error_node(state: ChatbotState) -> Dict[str, Any]:
    """Async error terminal.

    Unlike the sync version this returns only the three keys it changes. The
    sync node returns ``{**state, ...}``, which re-adds ``chat_history``
    through its ``operator.add`` reducer and duplicates the turn history.
    """
    logger.error("--- Entering Error State ---")
    error_message = str(state.get("error", "An unknown error occurred."))
    logger.error(f"Error details: {error_message}")
    user_facing_error = f"Sorry, an error occurred: {error_message}"
    return {"answer": user_facing_error, "retrieval_mode": "error", "error": error_message}


# --- Graph ----------------------------------------------------------------

def build_chatbot_graph_async(llm_instance):
    """Build the async twin of ``build_chatbot_graph``.

    Node names, conditional entry point and every edge mapping are identical
    to the sync graph so routing behaviour is preserved.
    """
    logger.info("Building the ASYNC chatbot graph...")
    global llm
    if not llm_instance:
        raise ValueError("LLM instance must be provided")
    llm = llm_instance

    graph = StateGraph(ChatbotState)

    graph.add_node("route_query", route_query_node)
    graph.add_node("retrieve_vectorstore", retrieve_vectorstore_node)
    graph.add_node("retrieve_web", retrieve_web_node)
    graph.add_node("generate_answer_rag", generate_answer_rag_node)
    graph.add_node("generate_llm_native", generate_llm_native_node)
    graph.add_node("handle_error", handle_error_node)

    graph.set_conditional_entry_point(
        route_or_generate,
        {
            "route_query": "route_query",
            "retrieve_vectorstore": "retrieve_vectorstore",
            "retrieve_web": "retrieve_web",
            "generate_llm_native": "generate_llm_native",
            "handle_error": "handle_error",
        },
    )

    graph.add_conditional_edges(
        "route_query",
        decide_after_router,
        {
            "retrieve_vectorstore": "retrieve_vectorstore",
            "retrieve_web": "retrieve_web",
            "generate_llm_native": "generate_llm_native",
            "handle_error": "handle_error",
        },
    )

    graph.add_conditional_edges(
        "retrieve_vectorstore",
        decide_after_vectorstore_retrieval,
        {
            "generate_answer_rag": "generate_answer_rag",
            "generate_llm_native": "generate_llm_native",
            "handle_error": "handle_error",
        },
    )

    graph.add_conditional_edges(
        "retrieve_web",
        decide_after_web_retrieval,
        {
            "generate_answer_rag": "generate_answer_rag",
            "generate_llm_native": "generate_llm_native",
            "handle_error": "handle_error",
        },
    )

    graph.add_edge("generate_answer_rag", END)
    graph.add_edge("generate_llm_native", END)
    graph.add_edge("handle_error", END)

    app = graph.compile()
    logger.info("ASYNC chatbot graph compiled successfully.")
    return app