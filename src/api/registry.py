"""Active-generation registry.

Tracks in-flight generations as ``conversation_id -> generation_id -> Task``.

Keying on a per-request ``generation_id`` (rather than on ``conversation_id``
alone) is what makes Stop safe against a stale request: if generation A is
cancelled and the user immediately sends message B on the same conversation,
B installs its own generation_id, and any late cleanup arriving for A can only
ever address A's entry -- never B's task.

The registry also enforces one live generation per conversation, so a
concurrent double-submit cannot leave two generators racing over the same
state.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Terminal states. A generation reaches exactly one of these and is never
# treated as another: notably `stopped` is NOT `completed` -- a stopped
# response carries partial text but the model never finished it.
STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"
STATUS_STOPPED = "stopped"
STATUS_FAILED = "failed"

TERMINAL_STATUSES = (STATUS_COMPLETED, STATUS_STOPPED, STATUS_FAILED)


@dataclass
class Generation:
    """One in-flight (or recently finished) generation."""

    conversation_id: str
    generation_id: str
    task: Optional["asyncio.Task"] = None
    status: str = STATUS_PENDING
    # Text accumulated so far. Kept on the generation so a Stop can still
    # report the partial answer after the task itself is gone.
    partial_answer: str = ""
    error: Optional[str] = None
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())

    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES


class GenerationRegistry:
    """conversation_id -> generation_id -> Generation."""

    def __init__(self) -> None:
        self._by_conversation: Dict[str, Dict[str, Generation]] = {}

    # -- registration ------------------------------------------------------
    def active_generation(self, conversation_id: str) -> Optional[Generation]:
        """The live generation for a conversation, if any.

        Only non-terminal generations are returned, so a finished generation
        can never be mistaken for a running one.
        """
        entries = self._by_conversation.get(conversation_id)
        if not entries:
            return None
        live = [g for g in entries.values() if not g.is_terminal()]
        if not live:
            return None
        return max(live, key=lambda g: g.created_at)

    def get(self, conversation_id: str, generation_id: str) -> Optional[Generation]:
        return self._by_conversation.get(conversation_id, {}).get(generation_id)

    def register(self, conversation_id: str, generation_id: Optional[str] = None) -> Generation:
        """Install a new pending generation for a conversation.

        Raises ``RuntimeError`` if the conversation already has a live
        generation -- the caller decides whether to reject or replace it.
        """
        existing = self.active_generation(conversation_id)
        if existing is not None:
            raise RuntimeError(
                f"Conversation {conversation_id} already has active generation {existing.generation_id}"
            )
        gen = Generation(
            conversation_id=conversation_id,
            generation_id=generation_id or uuid.uuid4().hex,
        )
        self._by_conversation.setdefault(conversation_id, {})[gen.generation_id] = gen
        logger.info(
            "Registered generation %s for conversation %s", gen.generation_id, conversation_id
        )
        return gen

    def attach_task(self, generation: Generation, task: "asyncio.Task") -> None:
        generation.task = task

    # -- terminal transitions ---------------------------------------------
    def finish(
        self,
        generation: Generation,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        """Move a generation to a terminal state (idempotent)."""
        if status not in TERMINAL_STATUSES:
            raise ValueError(f"Not a terminal status: {status}")
        if generation.is_terminal():
            return
        generation.status = status
        generation.error = error
        logger.info(
            "Generation %s (conversation %s) -> %s",
            generation.generation_id,
            generation.conversation_id,
            status,
        )

    # -- stop --------------------------------------------------------------
    async def stop(self, conversation_id: str, generation_id: Optional[str] = None) -> dict:
        """Cancel one specific generation.

        With ``generation_id`` the target is exact. Without it the currently
        active generation for the conversation is used, which is the common
        case (the UI knows the id it received, but a reconnecting client may
        not).
        """
        if generation_id:
            generation = self.get(conversation_id, generation_id)
            if generation is None:
                return {
                    "stopped": False,
                    "reason": "not_found",
                    "generation_id": generation_id,
                }
        else:
            generation = self.active_generation(conversation_id)
            if generation is None:
                return {"stopped": False, "reason": "no_active_generation"}

        if generation.is_terminal():
            return {
                "stopped": False,
                "reason": "already_finished",
                "generation_id": generation.generation_id,
                "status": generation.status,
            }

        task = generation.task
        if task is None or task.done():
            # Registered but never started (or already finished): no work to
            # cancel, so settle it as stopped to free the conversation.
            self.finish(generation, STATUS_STOPPED)
            return {"stopped": True, "generation_id": generation.generation_id, "status": STATUS_STOPPED}

        task.cancel()
        # Await the task so cancellation has fully unwound (LangGraph cancels
        # node futures and gathers background tasks in its `finally`) before we
        # report back. The task swallows CancelledError internally and always
        # terminates, so this cannot hang on cancellation.
        try:
            await asyncio.shield(asyncio.wait_for(asyncio.shield(task), timeout=10))
        except asyncio.TimeoutError:
            logger.error(
                "Generation %s did not settle within 10s of cancel", generation.generation_id
            )
        except asyncio.CancelledError:
            # If the *stop request itself* was cancelled (client hung up on the
            # stop endpoint), the generation is still being cancelled.
            raise
        except Exception as e:  # pragma: no cover - task records its own errors
            logger.warning("Generation %s raised during stop: %s", generation.generation_id, e)

        return {
            "stopped": True,
            "generation_id": generation.generation_id,
            "status": generation.status,
        }

    # -- cleanup -----------------------------------------------------------
    def release(self, conversation_id: str, generation_id: str) -> None:
        """Drop a finished generation's bookkeeping.

        Only removes the entry for this exact generation_id, so cleanup for a
        stale generation can never evict a newer one.
        """
        entries = self._by_conversation.get(conversation_id)
        if not entries:
            return
        entries.pop(generation_id, None)
        if not entries:
            self._by_conversation.pop(conversation_id, None)

    def active_summary(self) -> List[dict]:
        """Snapshot of live generations (used by tests and /api/health)."""
        out = []
        for conv_id, entries in self._by_conversation.items():
            for gen in entries.values():
                if not gen.is_terminal():
                    out.append(
                        {
                            "conversation_id": conv_id,
                            "generation_id": gen.generation_id,
                            "status": gen.status,
                        }
                    )
        return out


# Process-wide registry. A single uvicorn worker owns one event loop, so
# module scope is the correct lifetime for in-flight task handles.
registry = GenerationRegistry()