import time
import streamlit as st
from typing import Dict, Any, Optional

def typewriter(element, text: str, speed: int = 60):
    """Displays text character by character in a Streamlit element.

    Checks st.session_state.stop_requested each character — if True,
    the remaining text is flushed immediately and the flag is cleared.
    """
    placeholder = element.empty()
    displayed_text = ""
    delay = 1.0 / max(speed, 1)
    for char in text:
        # Check if the user pressed "Stop Generating"
        if st.session_state.get("stop_requested", False):
            # Show whatever we have so far (full text) and break
            displayed_text = text
            placeholder.markdown(displayed_text)
            st.session_state.stop_requested = False
            return
        displayed_text += char
        placeholder.markdown(displayed_text + "▌")
        time.sleep(delay)
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
