CSS_STYLE = """
    <style>
        /* =========================================================
           1. GENERAL BASELINE STYLES (Light Mode Defaults)
           ========================================================= */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
        .main > div:first-child {
            max-width: 900px;
            margin: auto;
            padding: 1.5rem 1rem 5rem 1rem;
        }
        .stApp > header {
            background-color: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(5px);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }
        hr {
            border-top: 1px solid #e9ecef;
            margin: 1rem 0;
        }

        /* --- Chat Messages (Light Mode) --- */
        div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) {
            margin-left: auto;
        }
        div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) > div[data-testid="stChatMessageContent"] {
            background-color: #007bff;
            color: #ffffff;
        }
        [data-testid="chatAvatarIcon-user"] {
            background-color: #0056b3 !important;
            color: #ffffff !important;
        }
        div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) {
            margin-right: auto;
        }
        div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) > div[data-testid="stChatMessageContent"] {
            background-color: #f1f3f5;
            color: #343a40;
        }
        [data-testid="chatAvatarIcon-assistant"] {
            background-color: #495057 !important;
            color: #ffffff !important;
        }
        .stChatMessage .stCaption {
            font-size: 0.75rem;
            color: #6c757d;
            padding-top: 8px;
            text-align: right;
        }
        div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) .stCaption {
            color: #b3d7ff;
        }

        /* --- Sidebar: Use Streamlit's own theme variables so it
              automatically follows light/dark mode --- */
        [data-testid="stSidebar"] {
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] .stTabs [data-testid="stMarkdownContainer"] p {
            font-weight: 600;
            font-size: 0.95rem;
        }
        [data-testid="stSidebar"] .stExpander {
            margin-bottom: 1rem;
            border-radius: 8px;
        }
        [data-testid="stSidebar"] .stExpander > summary {
            font-weight: 600;
            padding: 0.7rem 1rem !important;
            font-size: 0.95rem;
        }
        [data-testid="stSidebar"] .stButton>button {
            margin-top: 0.5rem;
        }

        /* --- Standard Buttons (Light Mode) --- */
        .stButton>button {
            border-radius: 8px;
            padding: 0.6rem 1rem;
            font-weight: 500;
            width: 100%;
            border: 1px solid #ced4da;
            background-color: #ffffff;
            color: #343a40;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            border-color: #adb5bd;
            background-color: #f1f3f5;
            color: #212529;
        }
        .stButton>button:active {
            transform: scale(0.98);
        }

        /* --- Selected/Active Mode Button (Highlighted Outline State - Light Mode) --- */
        .stButton>button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            border: 2px solid #007bff !important;
            background-color: #ebf5ff !important;
            color: #0056b3 !important;
            font-weight: 600 !important;
            box-shadow: 0 0 0 1px #007bff !important;
        }
        .stButton>button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            background-color: #dbeafe !important;
            border-color: #0056b3 !important;
            color: #004085 !important;
        }

        /* --- Special Action Buttons --- */
        .stButton>button:has(span>span:contains("Delete")) {
            background-color: #fdf2f2 !important;
            color: #dc3545 !important;
            border-color: #dc3545 !important;
        }
        .stButton>button:has(span>span:contains("Delete")):hover {
            background-color: #f8d7da !important;
            border-color: #b02a37 !important;
        }
        .stButton>button:has(span>span:contains("Rebuild")) {
            background-color: #f0f7ff !important;
            color: #17a2b8 !important;
            border-color: #17a2b8 !important;
        }
        .stButton>button:has(span>span:contains("Rebuild")):hover {
            background-color: #d1ecf1 !important;
            border-color: #117a8b !important;
        }

        /* --- Cursor Behaviors (Never Prohibited) --- */
        .stButton>button,
        .stButton>button:disabled,
        .stButton>button[disabled] {
            cursor: pointer !important;
            pointer-events: auto !important;
        }
        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] label * {
            cursor: pointer !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label {
            cursor: pointer !important;
        }

        /* --- Bottom chat bar ([data-testid="stBottom"]) ---
             Streamlit's native bottom container is already pinned to the
             bottom of the main content area (position: sticky), so it is
             centered together with the chat column and follows the sidebar
             in both light and dark modes. Do NOT force `position: fixed`
             with left/right: 0 here — that stretches the bar across the
             whole viewport and shifts it left of the chat column whenever
             the sidebar is expanded.                                    */

        /* --- Action buttons beside the chat input --- */
        [data-testid="stBottom"] [data-testid="stColumn"] .stButton>button {
            padding: 0.35rem 0.5rem !important;
            min-height: unset !important;
            height: 42px !important;
            font-size: 1.1rem !important;
            border-radius: 8px !important;
            line-height: 1 !important;
        }

        /* Chat history container with scroll */
        .chat-history-container {
            padding-bottom: 5rem;
        }

        /* Env var status styling (Light Mode) */
        .env-var-status {
            padding: 0.5rem;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }
        .env-var-status.valid {
            background-color: #e6f7ee;
            color: #0d6832;
        }
        .env-var-status.invalid {
            background-color: #fdf2f2;
            color: #9e2d2d;
        }
        .env-var-status.warning {
            background-color: #fff8e6;
            color: #8a6d3b;
        }

        /* =========================================================
           2. DARK MODE THEME ADJUSTMENTS
           Scoped to prefers-color-scheme: dark & Streamlit dark theme
           ========================================================= */
        @media (prefers-color-scheme: dark) {
            .stApp > header {
                background-color: rgba(14, 17, 23, 0.85) !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
            }
            hr {
                border-top-color: #2d323f !important;
            }

            /* Chat bubbles in dark mode */
            div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) > div[data-testid="stChatMessageContent"] {
                background-color: #262a36 !important;
                color: #e2e8f0 !important;
            }
            [data-testid="chatAvatarIcon-assistant"] {
                background-color: #374151 !important;
                color: #ffffff !important;
            }
            div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) > div[data-testid="stChatMessageContent"] {
                background-color: #0066cc !important;
                color: #ffffff !important;
            }
            .stChatMessage .stCaption {
                color: #9ca3af !important;
            }
            div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) .stCaption {
                color: #93c5fd !important;
            }

            /* Buttons in dark mode */
            .stButton>button {
                background-color: #262a36 !important;
                color: #e2e8f0 !important;
                border-color: #3d4354 !important;
            }
            .stButton>button:hover {
                background-color: #323746 !important;
                border-color: #525b72 !important;
                color: #ffffff !important;
            }

            /* Selected/Active Mode Button (Highlighted Outline State - Dark Mode) */
            .stButton>button[kind="primary"],
            button[data-testid="baseButton-primary"] {
                border: 2px solid #3b82f6 !important;
                background-color: rgba(59, 130, 246, 0.22) !important;
                color: #93c5fd !important;
                font-weight: 600 !important;
                box-shadow: 0 0 0 1px #3b82f6 !important;
            }
            .stButton>button[kind="primary"]:hover,
            button[data-testid="baseButton-primary"]:hover {
                background-color: rgba(59, 130, 246, 0.35) !important;
                border-color: #60a5fa !important;
                color: #bfdbfe !important;
            }

            /* Action buttons in dark mode */
            .stButton>button:has(span>span:contains("Delete")) {
                background-color: rgba(220, 53, 69, 0.2) !important;
                color: #ff8080 !important;
                border-color: #dc3545 !important;
            }
            .stButton>button:has(span>span:contains("Delete")):hover {
                background-color: rgba(220, 53, 69, 0.35) !important;
                border-color: #ff5c5c !important;
            }
            .stButton>button:has(span>span:contains("Rebuild")) {
                background-color: rgba(23, 162, 184, 0.2) !important;
                color: #5cdbf5 !important;
                border-color: #17a2b8 !important;
            }
            .stButton>button:has(span>span:contains("Rebuild")):hover {
                background-color: rgba(23, 162, 184, 0.35) !important;
                border-color: #38d1ee !important;
            }

            /* Env var status badges in dark mode */
            .env-var-status.valid {
                background-color: rgba(46, 125, 50, 0.25) !important;
                color: #81c784 !important;
                border: 1px solid rgba(76, 175, 80, 0.35) !important;
            }
            .env-var-status.invalid {
                background-color: rgba(198, 40, 40, 0.25) !important;
                color: #e57373 !important;
                border: 1px solid rgba(229, 115, 115, 0.35) !important;
            }
            .env-var-status.warning {
                background-color: rgba(245, 124, 0, 0.25) !important;
                color: #ffb74d !important;
                border: 1px solid rgba(255, 183, 77, 0.35) !important;
            }

        }

        /* =========================================================
           3. STREAMLIT EXPLICIT THEME SELECTORS ([data-theme="..."])
           ========================================================= */
        [data-theme="dark"] .stButton>button,
        .stApp[data-theme="dark"] .stButton>button {
            background-color: #262a36 !important;
            color: #e2e8f0 !important;
            border-color: #3d4354 !important;
        }
        /* Explicit Light Theme guards — reset to light defaults */
        [data-theme="light"] .stButton>button,
        .stApp[data-theme="light"] .stButton>button {
            background-color: #ffffff !important;
            color: #343a40 !important;
            border-color: #ced4da !important;
        }

        /* =========================================================
           4. CONVERSATION HISTORY SIDEBAR LIST
           ========================================================= */
        /* Compact conversation buttons in sidebar */
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton>button {
            margin-top: 0.1rem;
            margin-bottom: 0.1rem;
            padding: 0.35rem 0.6rem;
            font-size: 0.85rem;
            text-align: left;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        /* Small delete button beside each conversation */
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton>button {
            padding: 0.35rem 0.4rem;
            font-size: 0.75rem;
            min-width: unset;
            border-color: transparent;
            background-color: transparent !important;
            opacity: 0.5;
        }
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton>button:hover {
            opacity: 1;
            color: #dc3545 !important;
            background-color: transparent !important;
        }
    </style>
"""
