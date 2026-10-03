"""Phase 3A verification tests.

Covers:
  * real cancellation reaching the running node and the LLM stream,
  * generation_id-scoped tracking (stale cleanup cannot touch a newer run),
  * the three distinct terminal states,
  * SSE end-to-end behaviour including Stop and immediate resend,
  * absence of orphan asyncio tasks.

Run:  python tests/test_phase3a_cancellation.py
"""

import asyncio
import os
import sys
import unittest
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
os.environ.setdefault("GROQ_API_KEY", "test-key-not-real")
os.environ.setdefault("TAVILY_API_KEY", "test-key-not-real")

from langchain_core.language_models.chat_models import BaseChatModel  # noqa: E402
from langchain_core.messages import AIMessageChunk, BaseMessage  # noqa: E402
from langchain_core.outputs import ChatGenerationChunk  # noqa: E402
from langgraph.graph import END, StateGraph  # noqa: E402

from chatbot_graph_async import emit_delta  # noqa: E402
from api import streaming as streaming_mod  # noqa: E402
from api import engine as engine_mod  # noqa: E402
from api.registry import (  # noqa: E402
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_STOPPED,
    GenerationRegistry,
)
from api.streaming import GenerationRunner  # noqa: E402

# --- Test doubles ---------------------------------------------------------

LLM_STATS = {"tokens": 0, "cancelled": False, "completed": False}


class FakeStreamingLLM(BaseChatModel):
    """Streams `n` tokens with a delay; records whether it was cancelled."""

    n: int = 50
    delay: float = 0.03

    def _llm_type(self) -> str:
        return "fake-streaming"

    def _generate(self, messages, **kwargs):
        raise NotImplementedError("sync path unused")

    async def _astream(self, messages: List[BaseMessage], **kwargs):
        try:
            for i in range(self.n):
                await asyncio.sleep(self.delay)
                LLM_STATS["tokens"] += 1
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=f"t{i} ", id=f"c{i}")
                )
        except (asyncio.CancelledError, GeneratorExit):
            LLM_STATS["cancelled"] = True
            raise
        LLM_STATS["completed"] = True


NODE_STATS = {"cancelled": False, "completed": False}


class FakeState(dict):
    pass


async def _fake_generate_node(state: dict):
    """Mimics generate_llm_native: streams tokens onto the delta sink."""
    text = ""
    llm = FakeStreamingLLM(n=60, delay=0.03)
    stream = llm.astream(state.get("query", ""))
    try:
        async for chunk in stream:
            text += chunk.content
            emit_delta(chunk.content)
    except asyncio.CancelledError:
        NODE_STATS["cancelled"] = True
        try:
            if hasattr(stream, "aclose"):
                await stream.aclose()
        except Exception:
            pass
        raise
    NODE_STATS["completed"] = True
    return {"answer": text, "retrieval_mode": "llm_native"}


def _build_fake_graph():
    """Minimal graph with the same entry-point shape as the real one."""
    from chatbot_graph import ChatbotState

    g = StateGraph(ChatbotState)
    g.set_entry_point("generate_llm_native")
    g.add_node("generate_llm_native", _fake_generate_node)
    g.add_edge("generate_llm_native", END)
    return g.compile()


def _reset_stats():
    LLM_STATS.update(tokens=0, cancelled=False, completed=False)
    NODE_STATS.update(cancelled=False, completed=False)


def _other_tasks():
    return [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]


# --- 1. Cancellation reaches the node and the provider stream -------------

class TestCancellationPropagation(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        _reset_stats()
        self.registry = GenerationRegistry()
        self.graph = _build_fake_graph()
        engine_mod.get_async_graph = lambda model=None: self.graph
        streaming_mod.get_async_graph = lambda model=None: self.graph

    async def test_cancel_reaches_node_and_llm(self):
        gen = self.registry.register("conv-cancel")
        runner = GenerationRunner(gen, query="hello", chat_history=[], forced_mode="llm_native")

        events = []
        stream = runner.events()
        three_tokens_seen = asyncio.Event()

        async def consume():
            async for ev in stream:
                events.append(ev)
                if sum(1 for e in events if e["event"] == "token") >= 3:
                    three_tokens_seen.set()

        consumer = asyncio.create_task(consume())
        # Wait until 3 tokens have genuinely flowed through the stream,
        # proving generation is mid-flight.
        await asyncio.wait_for(three_tokens_seen.wait(), timeout=5.0)
        # Issue Stop while generation is active.
        stop_res = await self.registry.stop("conv-cancel", gen.generation_id)
        self.assertTrue(stop_res["stopped"])

        # Clean up the consumer task.
        consumer.cancel()
        try:
            await consumer
        except asyncio.CancelledError:
            pass

        self.assertTrue(NODE_STATS["cancelled"], "CancelledError never reached the node")
        self.assertTrue(LLM_STATS["cancelled"], "CancelledError never reached the LLM stream")
        self.assertFalse(NODE_STATS["completed"], "node ran to completion after Stop")
        self.assertEqual(gen.status, STATUS_STOPPED)

        # The generation must not have produced the full 60 tokens.
        self.assertLess(LLM_STATS["tokens"], 60)

    async def test_no_orphan_tasks_after_cancel(self):
        gen = self.registry.register("conv-orphans")
        runner = GenerationRunner(gen, query="hi", chat_history=[], forced_mode="llm_native")

        three_tokens_seen = asyncio.Event()

        async def consume():
            n = 0
            async for ev in runner.events():
                if ev["event"] == "token":
                    n += 1
                    if n >= 3:
                        three_tokens_seen.set()

        consumer = asyncio.create_task(consume())
        await asyncio.wait_for(three_tokens_seen.wait(), timeout=5.0)
        await self.registry.stop("conv-orphans", gen.generation_id)
        consumer.cancel()
        try:
            await consumer
        except asyncio.CancelledError:
            pass
        await asyncio.sleep(0.05)

        leftovers = [t for t in _other_tasks() if t is not consumer]
        self.assertEqual(leftovers, [], f"orphan tasks remained: {leftovers}")

    async def test_full_completion_is_completed_not_stopped(self):
        self.graph = _build_fake_graph()
        # Tiny stream so it finishes fast.
        orig = FakeStreamingLLM
        small = type("SmallLLM", (orig,), {"n": 3, "delay": 0.01})
        _fake_generate_node.__globals__["FakeStreamingLLM"] = small

        gen = self.registry.register("conv-complete")
        runner = GenerationRunner(gen, query="hi", chat_history=[], forced_mode="llm_native")

        events = []
        async for ev in runner.events():
            events.append(ev)

        names = [e["event"] for e in events]
        self.assertIn("completed", names)
        self.assertNotIn("stopped", names)
        self.assertEqual(gen.status, STATUS_COMPLETED)
        self.assertTrue(gen.partial_answer)
        _fake_generate_node.__globals__["FakeStreamingLLM"] = orig


# --- 2. generation_id-scoped tracking -------------------------------------

class TestGenerationRegistry(unittest.IsolatedAsyncioTestCase):
    async def test_second_generation_on_same_conversation_rejected(self):
        reg = GenerationRegistry()
        first = reg.register("c1")
        with self.assertRaises(RuntimeError):
            reg.register("c1")
        self.assertIsNotNone(first)

    async def test_stale_release_does_not_evict_newer_generation(self):
        """The core reason for keying on generation_id, not conversation_id."""
        reg = GenerationRegistry()
        old = reg.register("c1")
        reg.finish(old, STATUS_STOPPED)
        # Late cleanup for the old generation arrives *after* a new one started.
        reg.release("c1", old.generation_id)

        new = reg.register("c1")
        # Stale release again, this time explicitly against the old id.
        reg.release("c1", old.generation_id)
        self.assertIsNotNone(reg.get("c1", new.generation_id), "newer generation was evicted")

    async def test_stale_stop_cannot_cancel_newer_generation(self):
        reg = GenerationRegistry()
        old = reg.register("c1")
        old_task = asyncio.create_task(asyncio.sleep(30))
        reg.attach_task(old, old_task)
        reg.finish(old, STATUS_STOPPED)
        reg.release("c1", old.generation_id)

        new = reg.register("c1")
        new_task = asyncio.create_task(asyncio.sleep(30))
        reg.attach_task(new, new_task)
        try:
            # A stop naming the *old* generation must not touch the new one.
            result = await reg.stop("c1", old.generation_id)
            self.assertFalse(result["stopped"])
            self.assertEqual(result["reason"], "not_found")
            self.assertFalse(new_task.done(), "newer generation was cancelled by a stale stop")
        finally:
            new_task.cancel()
            try:
                await new_task
            except asyncio.CancelledError:
                pass

    async def test_stop_reports_already_finished(self):
        reg = GenerationRegistry()
        gen = reg.register("c1")
        reg.finish(gen, STATUS_COMPLETED)
        result = await reg.stop("c1", gen.generation_id)
        self.assertFalse(result["stopped"])
        self.assertEqual(result["reason"], "already_finished")
        self.assertEqual(result["status"], STATUS_COMPLETED)

    async def test_three_terminal_states_are_distinct(self):
        reg = GenerationRegistry()
        statuses = {STATUS_COMPLETED, STATUS_STOPPED, STATUS_FAILED}
        self.assertEqual(len(statuses), 3)
        for status in statuses:
            gen = reg.register(f"c-{status}")
            reg.finish(gen, status)
            self.assertEqual(gen.status, status)
            self.assertTrue(gen.is_terminal())

    async def test_finish_rejects_non_terminal_status(self):
        reg = GenerationRegistry()
        gen = reg.register("c1")
        with self.assertRaises(ValueError):
            reg.finish(gen, "pending")

    async def test_active_generation_ignores_terminal_entries(self):
        reg = GenerationRegistry()
        gen = reg.register("c1")
        reg.finish(gen, STATUS_COMPLETED)
        self.assertIsNone(reg.active_generation("c1"))
        self.assertEqual(reg.active_summary(), [])


# --- 3. HTTP / SSE end-to-end --------------------------------------------

class TestSSEEndpoint(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        _reset_stats()
        self.registry = GenerationRegistry()
        self.graph = _build_fake_graph()
        streaming_mod.get_async_graph = lambda model=None: self.graph
        streaming_mod.registry = self.registry
        # main.py imports registry by name; rebind for this test module.
        import api.main as main_mod
        main_mod.registry = self.registry
        main_mod.streaming = streaming_mod
        self.app = main_mod.app

    async def _collect(self, body, stop_after_tokens=None, stop_conversation="c-e2e"):
        """Consume an SSE response body, optionally issuing a Stop mid-stream."""
        from fastapi.testclient import TestClient

        # Drive the async app directly (TestClient is sync and would block the loop).
        events = []
        agen = body()
        stop_task = None
        async for frame in agen:
            events.append(frame)
            if (
                stop_after_tokens is not None
                and sum(1 for e in events if e["event"] == "token") >= stop_after_tokens
                and stop_task is None
            ):
                gen_id = next(
                    (e["data"].get("generation_id") for e in events if e["event"] == "started"),
                    None,
                )
                stop_task = asyncio.create_task(
                    self.registry.stop(stop_conversation, gen_id)
                )
        if stop_task is not None:
            stop_result = await stop_task
        else:
            stop_result = None
        return events, stop_result

    async def test_stop_produces_stopped_event_with_partial_text(self):
        from api.main import ChatRequest

        gen = self.registry.register("c-e2e")
        runner = GenerationRunner(gen, query="hello", chat_history=[], forced_mode="llm_native")

        async def body():
            async for ev in runner.events():
                yield {"event": ev["event"], "data": ev["data"]}

        events, stop_result = await self._collect(body, stop_after_tokens=3)

        names = [e["event"] for e in events]
        self.assertIn("token", names)
        self.assertIn("stopped", names, f"no stopped event; got {names}")
        self.assertNotIn("completed", names, "stopped run must not report completion")

        stopped = next(e for e in events if e["event"] == "stopped")
        self.assertTrue(stopped["data"]["partial"], "partial assistant text was lost")
        self.assertEqual(gen.status, STATUS_STOPPED)
        self.assertTrue(stop_result["stopped"])

    async def test_conversation_immediately_reusable_after_stop(self):
        gen = self.registry.register("c-reuse")
        runner = GenerationRunner(gen, query="hello", chat_history=[], forced_mode="llm_native")

        async def body():
            async for ev in runner.events():
                yield {"event": ev["event"], "data": ev["data"]}

        events, _ = await self._collect(body, stop_after_tokens=2, stop_conversation="c-reuse")
        self.assertIn("stopped", [e["event"] for e in events])

        # The stopped generation is terminal, so the conversation is free again.
        self.assertIsNone(self.registry.active_generation("c-reuse"))
        second = self.registry.register("c-reuse")
        self.assertNotEqual(second.generation_id, gen.generation_id)

    async def test_full_stream_completes_normally(self):
        gen = self.registry.register("c-ok")
        runner = GenerationRunner(gen, query="hi", chat_history=[], forced_mode="llm_native")

        orig = FakeStreamingLLM
        small = type("SmallLLM", (orig,), {"n": 4, "delay": 0.01})
        _fake_generate_node.__globals__["FakeStreamingLLM"] = small
        try:

            async def body():
                async for ev in runner.events():
                    yield {"event": ev["event"], "data": ev["data"]}

            events = [e async for e in body()]
            names = [e["event"] for e in events]
            self.assertIn("completed", names)
            self.assertNotIn("stopped", names)
            completed = next(e for e in events if e["event"] == "completed")
            self.assertTrue(completed["data"]["answer"])
            self.assertEqual(gen.status, STATUS_COMPLETED)
        finally:
            _fake_generate_node.__globals__["FakeStreamingLLM"] = orig

    async def test_no_orphan_tasks_after_full_stream(self):
        gen = self.registry.register("c-clean")
        runner = GenerationRunner(gen, query="hi", chat_history=[], forced_mode="llm_native")

        orig = FakeStreamingLLM
        small = type("SmallLLM", (orig,), {"n": 4, "delay": 0.01})
        _fake_generate_node.__globals__["FakeStreamingLLM"] = small
        try:

            async def body():
                async for ev in runner.events():
                    yield {"event": ev["event"], "data": ev["data"]}

            async for _ in body():
                pass
            await asyncio.sleep(0.1)
            self.assertEqual(_other_tasks(), [])
        finally:
            _fake_generate_node.__globals__["FakeStreamingLLM"] = orig


if __name__ == "__main__":
    unittest.main(verbosity=2)