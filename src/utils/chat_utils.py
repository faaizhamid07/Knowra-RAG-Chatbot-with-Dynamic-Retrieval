import time
import streamlit as st
from typing import Dict, Any, Optional

def typewriter(element, text: str, speed: int = 60):
    """Displays text progressively in chunks to minimize artificial latency.

    Checks st.session_state.stop_requested each chunk — if True,
    the remaining text is flushed immediately and the flag is cleared.
    """
    placeholder = element.empty()

    # Calculate chunk size based on text length to keep updates manageable (e.g. 15-20 updates total)
    chunk_size = max(8, int(len(text) / 20))
    chunk_size = min(chunk_size, 80) # Bound the chunk size

    # Target total artificial delay is ~1-1.5s max, instead of 20-30s
    num_updates = max(1, len(text) // chunk_size)
    chunk_delay = 1.2 / num_updates
    chunk_delay = min(chunk_delay, 0.04) # Cap delay at 40ms per chunk

    displayed_text = ""
    for i in range(0, len(text), chunk_size):
        if st.session_state.get("stop_requested", False):
            # Show full text immediately and break
            placeholder.markdown(text)
            st.session_state.stop_requested = False
            return

        chunk = text[i:i+chunk_size]
        displayed_text += chunk
        placeholder.markdown(displayed_text + "▌")
        time.sleep(chunk_delay)

    placeholder.markdown(displayed_text)

def get_chat_message_caption(message_data: Dict[str, Any]) -> Optional[str]:
    """Generate caption text for chat message based on mode and timing."""
    mode_display = message_data.get("mode", "unknown")
    time_taken = message_data.get("time", "")

    if mode_display == "error":
        return "⚠️ Error"
    elif mode_display in ["vectorstore", "web_search", "llm_native"]:
        mode_icon = "📚" if mode_display == "vectorstore" else "🌐" if mode_display == "web_search" else "💡"
        caption_text = f"{mode_icon} {mode_display.replace('_', ' ').title()}"
        if time_taken:
            caption_text += f" | {time_taken}"
        return caption_text
    return None
