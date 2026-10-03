"""Asynchronous topic title generator for RAG chatbot conversations.

Generates concise, informative 3-5 word topic titles (e.g. "Transformer Attention Explained")
based on the conversation content, running asynchronously in the background so it never blocks
or delays streaming token generation.
"""

import asyncio
import logging
import re
from typing import Optional

try:
    from ..config import GROQ_MODEL_NAME
except ImportError:
    from config import GROQ_MODEL_NAME

try:
    from .storage import get_conversation, update_conversation
except ImportError:
    from storage import get_conversation, update_conversation

logger = logging.getLogger(__name__)


def extract_heuristic_title(query: str) -> str:
    """Fast deterministic NLP heuristic fallback for topic extraction."""
    clean = query.strip()
    # Strip common leading conversational patterns
    patterns = [
        r"^(can you\s+)?(please\s+)?(explain|tell me about|what is|what are|how does|how do|describe|summarize|give me|write|help me with)\s+",
        r"^(i want to know about|could you explain|i need to understand)\s+",
        r"^(what\s+is\s+the\s+difference\s+between)\s+",
    ]
    topic = clean
    for pat in patterns:
        match = re.search(pat, topic, flags=re.IGNORECASE)
        if match:
            topic = topic[match.end():].strip()
            break

    # Capitalize words
    words = topic.split()
    if not words:
        return "New Chat"

    # Take first 4-6 meaningful words
    short_words = words[:6]
    title = " ".join(short_words).strip(" ?.,!;:-")
    # Title-case if all lowercase
    if title.islower():
        title = title.title()
    if len(title) > 40:
        title = title[:37].rsplit(" ", 1)[0] + "..."
    return title or "New Chat"


async def generate_topic_title(
    conversation_id: str,
    query: str,
    answer_snippet: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Generate a concise topic title for a conversation in the background."""
    try:
        # Check if conversation already has a customized title (not default or empty)
        conv = get_conversation(conversation_id)
        if conv and conv.get("title") not in (None, "", "New Chat", "Untitled Chat", "New Conversation"):
            existing = conv.get("title", "")
            # If title is already concise and custom, leave it
            if not existing.endswith("?") and len(existing.split()) <= 6 and len(existing) <= 40 and not existing.startswith("usr_"):
                return existing

        # First obtain heuristic title immediately as baseline and persist it
        heuristic_title = extract_heuristic_title(query)
        if heuristic_title and heuristic_title != "New Chat":
            update_conversation(conversation_id, title=heuristic_title)

        # Attempt fast LLM generation if Groq client is available
        try:
            import os
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage

            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                llm_model = model or os.getenv("GROQ_MODEL_NAME", GROQ_MODEL_NAME)
                llm = ChatGroq(
                    groq_api_key=groq_key,
                    model_name=llm_model,
                    temperature=0.2,
                    max_tokens=20,
                    timeout=5,
                )
                prompt = (
                    f'Generate a concise, descriptive 2-5 word topic title for this user query.\n'
                    f'Query: "{query[:200]}"\n'
                    f'Requirements:\n'
                    f'- 2 to 5 words max.\n'
                    f'- Title Case.\n'
                    f'- Do NOT use quotation marks.\n'
                    f'- Do NOT include words like "Question about", "Help with", or "Chat".\n'
                    f'- Plain topic only (e.g. "Transformer Attention Explained" or "Quantum Computing Basics").'
                )

                resp = await llm.ainvoke([
                    SystemMessage(content="You are an expert conversation topic title generator. Respond with ONLY the title."),
                    HumanMessage(content=prompt),
                ])
                raw_title = str(resp.content).strip().strip('"\'`')
                # Validate length and content
                if raw_title and len(raw_title) <= 50 and "\n" not in raw_title:
                    final_title = raw_title
                else:
                    final_title = heuristic_title
            else:
                final_title = heuristic_title
        except Exception as llm_err:
            logger.debug(
                "LLM title generation skipped (%s), using heuristic title: %s",
                llm_err,
                heuristic_title,
            )
            final_title = heuristic_title

        # Update conversation in storage
        update_conversation(conversation_id, title=final_title)
        logger.info("Updated conversation %s title -> '%s'", conversation_id, final_title)
        return final_title

    except Exception as e:
        logger.error("Error in generate_topic_title for %s: %s", conversation_id, e)
        return "New Chat"


def schedule_title_generation(
    conversation_id: str,
    query: str,
    answer_snippet: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    """Fire-and-forget helper to trigger title generation without awaiting."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(generate_topic_title(conversation_id, query, answer_snippet, model))
    except RuntimeError:
        # No running loop in current thread
        pass
