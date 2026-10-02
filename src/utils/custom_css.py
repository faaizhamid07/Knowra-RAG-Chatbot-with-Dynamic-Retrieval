CSS_STYLE = """
<style>
    /* =========================================================
       PHASE 4: FIGMA VISUAL REFINEMENT - COMPLETE REWRITE
       ========================================================= */

    /* 1. GLOBAL RESET & TYPOGRAPHY */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        letter-spacing: -0.01em;
    }

    /* Main Canvas: Warm gradient background */
    .main .block-container {
        max-width: 100% !important;
        background: linear-gradient(135deg, #F5F1E8 0%, #F9F7F3 100%) !important;
        padding: 0.4rem 1rem !important;  /* Reduced vertical padding */
    }

    .stApp {
        background: linear-gradient(135deg, #F5F1E8 0%, #F9F7F3 100%) !important;
    }

    /* Header Bar */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
    }

    /* =========================================================
       2. LEFT SIDEBAR (#080401 Deep Dark Theme)
       ========================================================= */
    section[data-testid="stSidebar"] {
        background-color: #080401 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
        background-color: #080401 !important;
        padding: 1.5rem 1rem !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: rgba(255, 255, 255, 0.65) !important;
        font-size: 0.8rem !important;
    }

    /* Sidebar Brand Header */
    .sidebar-header-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.75rem 1rem;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        margin-bottom: 1.25rem;
    }

    .sidebar-header-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.14);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }

    .sidebar-header-title {
        font-weight: 700;
        font-size: 1rem;
        color: #FFFFFF;
    }

    /* Sidebar Tabs */
    section[data-testid="stSidebar"] [data-testid="stTabs"] button[role="tab"] {
        color: rgba(255, 255, 255, 0.6) !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        border-bottom: 2px solid transparent !important;
        padding: 0.5rem 0.8rem !important;
    }

    section[data-testid="stSidebar"] [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #FE842B !important;
        border-bottom: 2px solid #FE842B !important;
    }

    /* Sidebar Inputs */
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.07) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }

    /* Sidebar File Uploader */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px dashed rgba(255, 255, 255, 0.2) !important;
        border-radius: 14px !important;
        padding: 1rem !important;
    }

    section[data-testid="stSidebar"] [data-testid="stFileUploader"] section * {
        color: rgba(255, 255, 255, 0.85) !important;
    }

    /* Sidebar Buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.55rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.16) !important;
        border-color: #FE842B !important;
        color: #FFFFFF !important;
    }

    /* RAG Engine Status Card */
    .sidebar-status-card {
        background: linear-gradient(114.05deg, rgba(254, 131, 42, 0.12) 24.79%, rgba(254, 131, 42, 0.28) 43.95%, rgba(254, 131, 42, 0.12) 64.65%) !important;
        border: 1px solid rgba(254, 131, 42, 0.25) !important;
        border-radius: 18px 36px 18px 18px !important;
        padding: 1rem 1.1rem !important;
        margin-top: 1.5rem !important;
        backdrop-filter: blur(8px) !important;
    }

    .sidebar-status-badge {
        display: inline-block;
        background: linear-gradient(120deg, #FE842B, #FFA756);
        color: #FFFFFF;
        font-size: 0.65rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        padding: 2px 8px;
        border-radius: 8px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .sidebar-status-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #FFFFFF;
        margin-bottom: 2px;
    }

    .sidebar-status-desc {
        font-size: 0.78rem;
        color: rgba(255, 255, 255, 0.75);
        line-height: 1.35;
    }

    /* =========================================================
       3. CENTER MAIN CHAT AREA - VISUAL REFINEMENT
       ========================================================= */

    /* Header Area - Prominent and clear */
    /* Target Streamlit's actual title structure with high specificity */
    .stApp [data-testid="stAppViewContainer"] h1,
    .stApp .main h1,
    section.main h1,
    .stApp h1 {
        color: #0F172A !important;  /* Dark, readable */
        font-size: 2.5rem !important;  /* Large but not oversized */
        font-weight: 800 !important;   /* Bold */
        line-height: 1.15 !important; /* Tight line height */
        letter-spacing: -0.02em !important;
        margin: 0.4rem 0 0.3rem 0 !important; /* Proper spacing */
        opacity: 1 !important;         /* Fully opaque */
        text-align: left !important;
        visibility: visible !important;
        display: block !important;
    }

    /* Subtitle/caption - clear but secondary */
    .stApp [data-testid="stCaptionContainer"],
    .stApp .stCaption {
        color: #475569 !important;   /* Medium gray for hierarchy */
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        margin: 0 0 1rem 0 !important; /* Compact bottom margin */
        opacity: 1 !important;        /* Fully visible */
        line-height: 1.3 !important;
    }

    /* Mode Toggle Row - Proper spacing and alignment */
    div[data-testid="stHorizontalBlock"]:has(button[key="btn_mode_chat"]) {
        margin-bottom: 1rem !important;  /* More compact spacing */
    }

    /* Mode Toggle Buttons - Compact and small */
    /* Target by Streamlit key classes in grandparent */
    .st-key-btn_mode_chat .stButton > button,
    .st-key-btn_mode_eval .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        padding: 0.3rem 0.6rem !important;
        height: auto !important;
        min-height: unset !important;
        transition: all 0.2s ease !important;
    }

    /* Empty State Hero - Vertically compact, properly spaced */
    .empty-state-hero {
        text-align: center;
        padding: 0.8rem !important;  /* Reduced vertical padding */
        margin: 0.3rem 0 0.8rem 0 !important;  /* Minimal margins */
    }

    .empty-state-icon {
        font-size: 2rem !important;  /* Compact icon */
        margin-bottom: 0.25rem !important;
        display: inline-block;
        filter: drop-shadow(0 2px 6px rgba(254, 132, 43, 0.1));
    }

    .empty-state-title {
        font-size: 1.5rem !important;  /* Prominent but not oversized */
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.3rem !important;
        line-height: 1.2 !important;
        text-align: center !important;
    }

    .empty-state-desc {
        font-size: 0.85rem !important;  /* Readable but compact */
        color: #475569 !important;   /* Clear but secondary */
        max-width: 460px !important;
        margin: 0 auto 0.6rem auto !important;  /* Reduced bottom margin */
        line-height: 1.4 !important;
        opacity: 1 !important;        /* Fully visible */
        text-align: center !important;
    }

    /* Suggestion Cards - Compact and visually refined */
    .st-key-suggestion_0 .stButton > button,
    .st-key-suggestion_1 .stButton > button,
    .st-key-suggestion_2 .stButton > button,
    .st-key-suggestion_3 .stButton > button {
        background: #FFFFFF !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 14px !important;
        padding: 0.75rem 1rem !important;  /* Slightly more balanced padding */
        text-align: left !important;
        color: #1E293B !important;
        font-size: 0.85rem !important;  /* Slightly larger font */
        font-weight: 500 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
        height: auto !important;
        min-height: 44px !important;
        line-height: 1.3 !important;
    }

    .st-key-suggestion_0 .stButton > button:hover,
    .st-key-suggestion_1 .stButton > button:hover,
    .st-key-suggestion_2 .stButton > button:hover,
    .st-key-suggestion_3 .stButton > button:hover {
        border-color: #FE842B !important;
        background: rgba(254, 132, 43, 0.05) !important;
        box-shadow: 0 4px 12px rgba(254, 132, 43, 0.12) !important;
        transform: translateY(-2px);
    }

    /* Chat Messages */
    .chat-history-container {
        padding-bottom: 1rem;
        min-height: 150px;
    }

    /* User Message Bubble */
    div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) {
        margin-left: auto !important;
        max-width: 85% !important;
        background: transparent !important;
        border: none !important;
    }

    div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) > div[data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #1E293B, #0F172A) !important;
        color: #FFFFFF !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 0.7rem 1rem !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06) !important;
    }

    div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) > div[data-testid="stChatMessageContent"] * {
        color: #FFFFFF !important;
    }

    [data-testid="chatAvatarIcon-user"] {
        background: #0F172A !important;
        color: #FFFFFF !important;
    }

    /* Assistant Message Bubble */
    div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) {
        margin-right: auto !important;
        max-width: 90% !important;
        background: transparent !important;
        border: none !important;
    }

    div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) > div[data-testid="stChatMessageContent"] {
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 0.8rem 1.1rem !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
    }

    [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #40A3EC, #FE842B) !important;
        color: #FFFFFF !important;
    }

    /* Citation & Mode Badges */
    .stChatMessage .stCaption {
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        padding: 2px 8px !important;
        border-radius: 8px !important;
        background: rgba(254, 132, 43, 0.08) !important;
        color: #C2410C !important;
        border: 1px solid rgba(254, 132, 43, 0.15) !important;
        margin-top: 5px !important;
    }

    /* Glowing Input Composer - styled on the REAL keyed container.
       Streamlit renders st.container(key=...) as
         div.st-key-chat_input_container > div.stVerticalBlock
       A fake HTML wrapper div produced zero children, which is why the
       surface styling never enclosed anything before. */
    .st-key-chat_input_container {
        background: #FFFFFF !important;
        border: 1px solid rgba(15, 23, 42, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04),
                    0 4px 12px rgba(15, 23, 42, 0.05) !important;
        padding: 0.4rem 0.5rem !important;
        margin-top: 0.5rem !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    .st-key-chat_input_container:focus-within {
        border-color: rgba(254, 132, 43, 0.5) !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04),
                    0 6px 18px rgba(254, 132, 43, 0.1) !important;
    }

    /* Keep Streamlit's own chat input chrome transparent inside our surface */
    .st-key-chat_input_container [data-testid="stChatInput"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    .st-key-chat_input_container [data-testid="stChatInput"] textarea,
    .st-key-chat_input_container [data-testid="stChatInput"] [contenteditable="true"] {
        background: transparent !important;
        color: #0F172A !important;
        font-size: 0.92rem !important;
        caret-color: #FE842B !important;
    }

    /* Submission arrow: subtle, not a heavy dark blob */
    .st-key-chat_input_container [data-testid="stChatInputSubmitButton"] {
        background: rgba(15, 23, 42, 0.06) !important;
        color: #0F172A !important;
        border-radius: 50% !important;
        transition: all 0.15s ease !important;
    }

    .st-key-chat_input_container [data-testid="stChatInputSubmitButton"]:hover {
        background: #FE842B !important;
        color: #FFFFFF !important;
    }

    /* Input composer action buttons (stop / clear) */
    .st-key-chat_input_container .st-key-stop_gen .stButton > button,
    .st-key-chat_input_container .st-key-clear_chat .stButton > button {
        border-radius: 9px !important;
        height: 32px !important;
        min-height: unset !important;
        padding: 0 !important;
        width: 32px !important;
        font-size: 0.85rem !important;
        border: 1px solid rgba(15, 23, 42, 0.08) !important;
        background-color: #F8FAFC !important;
        transition: all 0.15s ease !important;
    }

    .st-key-chat_input_container .st-key-stop_gen .stButton > button:hover {
        background-color: rgba(254, 132, 43, 0.1) !important;
        border-color: #FE842B !important;
    }

    .st-key-chat_input_container .st-key-clear_chat .stButton > button:hover {
        background-color: rgba(239, 68, 68, 0.08) !important;
        border-color: #EF4444 !important;
    }

    /* Legacy fake-div selectors kept harmless */
    .chat-input-container,
    .composer-inner {
        background: #FFFFFF !important;
        border-radius: 16px !important;
    }

    /* =========================================================
       4. RIGHT HISTORY SIDEBAR PANEL - Genuine enclosing surface
       Streamlit renders st.container(key=...) as:
         div.st-key-right_history_panel > div.stVerticalBlock
       so we style the keyed wrapper, not a fake HTML div.
       ========================================================= */
    /* Streamlit's stLayoutWrapper hugs its content by default, so the panel
       collapses to ~170px. Stretch the wrapper, then the panel fills it. */
    [data-testid="stLayoutWrapper"]:has(> div > .st-key-right_history_panel) {
        height: 100% !important;
        align-self: stretch !important;
    }

    div.st-key-right_history_panel.stVerticalBlock {
        background: linear-gradient(160deg, #FFFDFB 0%, #FAF5F0 100%) !important;
        border: 1px solid rgba(15, 23, 42, 0.08) !important;
        border-radius: 18px !important;
        padding: 1rem 0.85rem !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04),
                    0 8px 24px rgba(15, 23, 42, 0.05) !important;
        height: 100% !important;
        min-height: 420px !important;
        align-self: stretch !important;
        overflow-y: auto !important;
    }

    /* Title row inside the history panel */
    .st-key-right_history_panel .history-panel-title {
        font-size: 0.8rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(15, 23, 42, 0.07);
        margin-bottom: 0.7rem;
    }

    .st-key-right_history_panel .history-separator {
        height: 1px;
        background: rgba(15, 23, 42, 0.07);
        margin: 0.7rem 0;
    }

    .st-key-right_history_panel .history-date-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        margin: 0.2rem 0 0.45rem 0;
    }

    .st-key-right_history_panel .history-empty-note {
        font-size: 0.78rem;
        color: #94A3B8;
        line-height: 1.5;
        padding: 0.4rem 0.1rem;
    }

    /* Legacy: keep .right-history-panel rules harmless if markup returns */
    .right-history-panel {
        background: linear-gradient(160deg, #FFFDFB 0%, #FAF5F0 100%) !important;
        border-radius: 18px !important;
    }

    .history-panel-title {
        font-size: 0.8rem;
        font-weight: 800;
        color: #0F172A;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }

    /* New Chat Button - Accent with proper styling */
    .st-key-btn_new_chat .stButton > button {
        background: linear-gradient(135deg, #40A3EC 0%, #FE842B 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 0.8rem !important;
        box-shadow: 0 3px 10px rgba(254, 132, 43, 0.2) !important;
        transition: all 0.2s ease !important;
    }

    .st-key-btn_new_chat .stButton > button:hover {
        box-shadow: 0 4px 14px rgba(254, 132, 43, 0.3) !important;
        transform: translateY(-1px);
    }

    /* History Section Date Headers */
    .history-date-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin: 0.8rem 0 0.4rem 0.2rem;
    }

    /* Conversation Navigation Items */
    .st-key-right_history_panel [data-testid="stHorizontalBlock"] .stButton > button {
        background: #FFFFFF !important;
        border: 1px solid rgba(15, 23, 42, 0.07) !important;
        border-radius: 10px !important;
        color: #334155 !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 0.5rem 0.65rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        transition: all 0.15s ease !important;
    }

    .st-key-right_history_panel [data-testid="stHorizontalBlock"] .stButton > button:hover {
        background: #F8FAFC !important;
        border-color: rgba(15, 23, 42, 0.15) !important;
        color: #0F172A !important;
    }

    /* Active conversation item inside the real panel */
    .st-key-right_history_panel .st-key-right_history_panel button[data-testid="stBaseButton-primary"],
    .st-key-right_history_panel button[data-testid="stBaseButton-primary"] {
        background: rgba(15, 23, 42, 0.06) !important;
        border: 1px solid rgba(15, 23, 42, 0.18) !important;
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* Active Conversation Item */
    .st-key-right_history_panel button[data-testid="stBaseButton-primary"] {
        background: rgba(15, 23, 42, 0.07) !important;
        border: 1px solid rgba(15, 23, 42, 0.2) !important;
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    /* Delete Button in History */
    .st-key-right_history_panel [data-testid="stColumn"]:last-child .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #94A3B8 !important;
        padding: 0.5rem 0.3rem !important;
        font-size: 0.72rem !important;
        box-shadow: none !important;
    }

    .st-key-right_history_panel [data-testid="stColumn"]:last-child .stButton > button:hover {
        color: #EF4444 !important;
        background: rgba(239, 68, 68, 0.1) !important;
        border-radius: 8px !important;
    }

    /* =========================================================
       5. STATUS & UTILITY BADGES
       ========================================================= */
    .env-var-status {
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
        margin-bottom: 0.75rem;
        font-size: 0.82rem;
        font-weight: 500;
    }

    .env-var-status.valid {
        background-color: rgba(34, 197, 94, 0.12);
        color: #4ADE80;
        border: 1px solid rgba(34, 197, 94, 0.25);
    }

    .env-var-status.invalid {
        background-color: rgba(239, 68, 68, 0.12);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.25);
    }

    /* =========================================================
       6. DARK MODE OVERRIDES
       ========================================================= */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #0F1117 !important;
            color: #F1F5F9 !important;
        }

        .main .block-container {
            background: #0F1117 !important;
        }

        .app-main-title,
        .empty-state-title {
            color: #F8FAFC !important;
        }

        .app-main-subtitle,
        .empty-state-desc {
            color: #94A3B8 !important;
        }

        .suggestion-card-btn .stButton > button {
            background: #1A1D27 !important;
            border-color: rgba(255, 255, 255, 0.08) !important;
            color: #F1F5F9 !important;
        }

        .suggestion-card-btn .stButton > button:hover {
            background: rgba(254, 132, 43, 0.08) !important;
            border-color: #FE842B !important;
        }

        div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) > div[data-testid="stChatMessageContent"] {
            background: #1A1D27 !important;
            color: #F8FAFC !important;
            border-color: rgba(255, 255, 255, 0.08) !important;
        }

        .st-key-chat_input_container {
            background: #1A1D27 !important;
            border-color: rgba(254, 132, 43, 0.4) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }

        .st-key-chat_input_container [data-testid="stChatInput"] textarea,
        .st-key-chat_input_container [data-testid="stChatInput"] [contenteditable="true"] {
            color: #F1F5F9 !important;
        }

        .right-history-panel {
            background: linear-gradient(135deg, #151821 0%, #1A1F2E 100%) !important;
            border-color: rgba(254, 132, 43, 0.25) !important;
        }

        .history-panel-title {
            color: #F8FAFC !important;
        }

        .right-history-panel [data-testid="stHorizontalBlock"] .stButton > button {
            background: #1E2330 !important;
            border-color: rgba(255, 255, 255, 0.06) !important;
            color: #E2E8F0 !important;
        }

        .st-key-right_history_panel.stVerticalBlock {
            background: linear-gradient(160deg, #151821 0%, #1A1F2E 100%) !important;
            border-color: rgba(255, 255, 255, 0.08) !important;
        }

        .st-key-right_history_panel .history-panel-title,
        .st-key-right_history_panel .history-date-label {
            color: #F8FAFC !important;
        }

        .st-key-right_history_panel [data-testid="stHorizontalBlock"] .stButton > button {
            background: #1E2330 !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            color: #E2E8F0 !important;
        }

        .st-key-right_history_panel [data-testid="stHorizontalBlock"] .stButton > button:hover {
            background: #282E3F !important;
            color: #FFFFFF !important;
        }
    }
</style>
"""
