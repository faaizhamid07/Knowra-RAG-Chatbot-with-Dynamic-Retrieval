"""Streaming driver: runs one generation and reports its lifecycle.

``GenerationRunner`` owns the asyncio task for a single request. It bridges
three things:

1. the RAG graph, executed via ``graph.astream(stream_mode="updates")`` so
   cancellation stays wired to the running node;
2. an ``asyncio.Queue`` that generation nodes push token deltas onto via the
   contextvar sink, and that this class drains; and
3. the generation registry, so the caller can cancel exactly this generation.

Every run ends in exactly one terminal state -- ``completed``, ``stopped`` or
``failed`` -- and the run always puts a matching terminal event on the queue
so the SSE stream can never hang.
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator, Dict, List, Optional

try:  # package-relative (imported as src.api.streaming)
    from ..chatbot_graph_async import reset_delta_sink, set_delta_sink
except ImportError:  # flat import (PYTHONPATH=src)
    from chatbot_graph_async import reset_delta_sink, set_delta_sink

try:
    from .engine import get_async_graph
    from .registry import (
        STATUS_COMPLETED,
        STATUS_FAILED,
        STATUS_STOPPED,
        Generation,
        registry,
    )
except ImportError:  # flat import
    from engine import get_async_graph
    from registry import (
        STATUS_COMPLETED,
        STATUS_FAILED,
        STATUS_STOPPED,
        Generation,
        registry,
    )

logger = logging.getLogger(__name__)

# Terminal sentinel placed on the queue to close the stream.
_DONE = "__done__"


class GenerationRunner:
    """Drives one generation from query to a terminal state."""

    def __init__(
        self,
        generation: Generation,
        query: str,
        chat_history: List[Dict[str, str]],
        forced_mode: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.generation = generation
        self.query = query
        self.chat_history = chat_history or []
        self.forced_mode = forced_mode
        self.model = model
        self.queue: asyncio.Queue = asyncio.Queue()
        # Every delta the model has produced, kept as it streams. This is the
        # authoritative partial text: on Stop the task is cancelled, so the
        # graph never writes a final answer to state and the accumulated
        # stream is the only record of what the user had already received.
        self.emitted: List[str] = []
        self.started_at = time.time()

    # -- public API --------------------------------------------------------
    async def events(self) -> AsyncIterator[dict]:
        """Yield SSE payloads until the generation reaches a terminal state."""
        task = asyncio.create_task(self._run())
        registry.attach_task(self.generation, task)

        try:
            while True:
                item = await self.queue.get()
                if item is _DONE:
                    break
                yield item
        except asyncio.CancelledError:
            # The HTTP client disconnected without pressing Stop. Treat it as
            # a stop so no generation keeps running with nobody listening.
            logger.info(
                "SSE consumer for generation %s disconnected; cancelling",
                self.generation.generation_id,
            )
            if not task.done():
                task.cancel()
            raise
        finally:
            # Belt and braces: the task always settles itself, but ensure the
            # loop never retains a live task for a closed stream.
            if not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):  # noqa: B014
                    pass

    def result(self) -> Dict[str, object]:
        """The non-streamed summary of how this generation ended."""
        gen = self.generation
        return {
            "generation_id": gen.generation_id,
            "conversation_id": gen.conversation_id,
            "status": gen.status,
            "answer": gen.partial_answer,
            "error": gen.error,
            "elapsed": round(time.time() - self.started_at, 3),
        }

    # -- internals ---------------------------------------------------------
    def _emit(self, event: str, **payload) -> None:
        self.queue.put_nowait({"event": event, "data": payload})

    async def _run(self) -> None:
        """Execute the graph. Never raises; always ends in a terminal state."""
        gen = self.generation

        def _sink(text: str) -> None:
            # Called from inside the running node, once per provider delta.
            # Accumulate first so a Stop can always report what was produced,
            # even if the queue is momentarily full or the consumer has gone.
            self.emitted.append(text)
            self.queue.put_nowait({"event": "token", "data": {"delta": text}})

        sink_token = set_delta_sink(_sink)
        citations: List[str] = []
        last_mode: Optional[str] = None
        try:
            graph = get_async_graph(self.model) if self.model else get_async_graph()
            self._emit(
                "started",
                generation_id=gen.generation_id,
                conversation_id=gen.conversation_id,
                model=self.model,
            )

            final_state: Dict[str, object] = {}

            async for _update in graph.astream(
                {
                    "query": self.query,
                    "chat_history": self.chat_history,
                    "forced_mode": self.forced_mode,
                },
                stream_mode="updates",
            ):
                # Report routing/mode and sources as soon as they are known so
                # the UI can label the in-flight bubble.
                final_state = _merge_state(final_state, _update)
                mode = final_state.get("retrieval_mode")
                if mode and mode != last_mode:
                    last_mode = str(mode)
                    self._emit("retrieval", retrieval_mode=mode)
                if final_state.get("generation_source") == "web_search" and not citations:
                    citations = _extract_urls(final_state.get("documents") or [])
                    if citations:
                        self._emit("sources", sources=citations)

            answer = str(final_state.get("answer") or "")
            gen.partial_answer = answer
            self.emitted = [answer]
            err = final_state.get("error")
            retrieval_mode = str(final_state.get("retrieval_mode") or last_mode or "unknown")

            if err or retrieval_mode == "error":
                # The graph reached its own error terminal: a genuine failure.
                registry.finish(gen, STATUS_FAILED, error=str(err) if err else "unknown error")
                self._emit(
                    "error",
                    message=str(answer or err),
                    retrieval_mode=retrieval_mode,
                    generation_id=gen.generation_id,
                    partial=gen.partial_answer,
                )
            else:
                registry.finish(gen, STATUS_COMPLETED)
                self._emit(
                    "completed",
                    answer=answer,
                    retrieval_mode=retrieval_mode,
                    generation_id=gen.generation_id,
                    elapsed=round(time.time() - self.started_at, 3),
                    sources=citations,
                )

        except asyncio.CancelledError:
            # Stop pressed (or the transport vanished). The partial text
            # already streamed to the client stays on the generation and is
            # reported here; the state is `stopped`, never `completed`.
            partial = gen.partial_answer or "".join(self.emitted)
            gen.partial_answer = partial
            registry.finish(gen, STATUS_STOPPED)
            self._emit(
                "stopped",
                partial=partial,
                generation_id=gen.generation_id,
                message="Generation stopped by user.",
            )
            return

        except Exception as e:  # noqa: BLE001
            logger.exception("Generation %s failed", gen.generation_id)
            gen.partial_answer = gen.partial_answer or "".join(self.emitted)
            registry.finish(gen, STATUS_FAILED, error=str(e))
            self._emit(
                "error",
                message=str(e),
                generation_id=gen.generation_id,
                partial=gen.partial_answer,
            )
        finally:
            reset_delta_sink(sink_token)
            # Always close the queue so the SSE stream terminates even if a
            # terminal emit above was somehow skipped.
            self.queue.put_nowait(_DONE)

    def _merge_state(self, acc: Dict[str, object], update: object) -> Dict[str, object]:
        return _merge_state(acc, update)


def _merge_state(acc: Dict[str, object], update: object) -> Dict[str, object]:
    """Fold one ``stream_mode="updates"`` payload into an accumulated state.

    ``updates`` yields ``{node_name: {key: value}}``. Values are treated as
    last-write-wins except ``chat_history``, which the graph appends via its
    reducer and which we do not need for the event payload.
    """
    if not isinstance(update, dict):
        return acc
    for node_delta in update.values():
        if isinstance(node_delta, dict):
            for key, value in node_delta.items():
                if key == "chat_history":
                    continue
                acc[key] = value
    return acc


def _extract_urls(documents: List[object]) -> List[str]:
    urls: List[str] = []
    for doc in documents:
        if not isinstance(doc, str):
            continue
        for line in doc.splitlines():
            line = line.strip()
            if line.startswith("Source URL:"):
                url = line.split("Source URL:", 1)[1].strip()
                if url and url != "N/A" and url not in urls:
                    urls.append(url)
    return urls


def sse_payload(event: str, data: Dict[str, object]) -> str:
    """Serialize one SSE frame."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
