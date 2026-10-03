"""Conversation storage management for the FastAPI backend.

Provides durable JSON file-backed conversation persistence for multi-turn chats.
"""

import json
import logging
import os
import threading
import time
import uuid
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Absolute path rooted at repository root/data/conversations.json
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONVERSATIONS_FILE = os.path.join(_project_root, "data", "conversations.json")
_lock = threading.Lock()


def _ensure_data_dir() -> None:
    os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)


def _load_all() -> Dict[str, dict]:
    _ensure_data_dir()
    if not os.path.exists(CONVERSATIONS_FILE):
        return {}
    try:
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception as e:
        logger.error("Error loading conversations from %s: %s", CONVERSATIONS_FILE, e)
        return {}


def _save_all(data: Dict[str, dict]) -> None:
    _ensure_data_dir()
    try:
        temp_file = f"{CONVERSATIONS_FILE}.tmp.{os.getpid()}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Atomic replace
        os.replace(temp_file, CONVERSATIONS_FILE)
    except Exception as e:
        logger.error("Error saving conversations to %s: %s", CONVERSATIONS_FILE, e)


def list_conversations() -> List[dict]:
    with _lock:
        data = _load_all()
        result = []
        for cid, conv in data.items():
            result.append({
                "id": cid,
                "title": conv.get("title", "New Chat"),
                "created_at": conv.get("created_at", time.time()),
                "updated_at": conv.get("updated_at", conv.get("created_at", time.time())),
                "message_count": len(conv.get("messages", [])),
                "last_message": (
                    conv.get("messages")[-1]["content"][:60]
                    if conv.get("messages")
                    else ""
                ),
            })
        # Sort by latest update time descending
        result.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return result


def get_conversation(conversation_id: str) -> Optional[dict]:
    with _lock:
        data = _load_all()
        if conversation_id not in data:
            return None
        return data[conversation_id]


def create_conversation(conversation_id: Optional[str] = None, title: str = "New Chat") -> dict:
    with _lock:
        data = _load_all()
        cid = conversation_id or str(uuid.uuid4())
        now = time.time()
        conv = {
            "id": cid,
            "title": title,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        data[cid] = conv
        _save_all(data)
        return conv


def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    messages: Optional[List[dict]] = None,
) -> Optional[dict]:
    with _lock:
        data = _load_all()
        now = time.time()
        if conversation_id not in data:
            # Create if does not exist
            data[conversation_id] = {
                "id": conversation_id,
                "title": title or "New Chat",
                "messages": messages or [],
                "created_at": now,
                "updated_at": now,
            }
        else:
            if title is not None:
                data[conversation_id]["title"] = title
            if messages is not None:
                data[conversation_id]["messages"] = messages
            data[conversation_id]["updated_at"] = now

        _save_all(data)
        return data[conversation_id]


def delete_conversation(conversation_id: str) -> bool:
    with _lock:
        data = _load_all()
        if conversation_id in data:
            del data[conversation_id]
            _save_all(data)
            return True
        return False


def append_message(conversation_id: str, message: dict) -> dict:
    with _lock:
        data = _load_all()
        now = time.time()
        if conversation_id not in data:
            data[conversation_id] = {
                "id": conversation_id,
                "title": "New Chat",
                "messages": [message],
                "created_at": now,
                "updated_at": now,
            }
        else:
            data[conversation_id]["messages"].append(message)
            data[conversation_id]["updated_at"] = now

        _save_all(data)
        return data[conversation_id]
