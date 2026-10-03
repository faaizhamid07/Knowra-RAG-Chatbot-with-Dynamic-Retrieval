# Knowra Frontend

Modern, high-performance React 19 + TypeScript SPA for Knowra (Multi-Source RAG Chatbot with Dynamic Retrieval).

## Features

- **Real-Time Token Streaming:** Server-Sent Events (SSE) consumer with instant token rendering and latency counters.
- **Dynamic Retrieval Badges:** Live badges indicating retrieval route (`LLM Native`, `Vectorstore`, `Web Search`).
- **Interactive Control Bar:** Instant model selection, dynamic vs forced retrieval mode overrides, and system status indicators.
- **Real Stop / Socket Abort:** Abort active generation with instant partial response preservation and immediate follow-up readiness.
- **Session & Thread Management:** Multi-conversation sidebar with auto-generated concise topic titles.
- **Document & Vectorstore Management Modal:** Ingest, view, delete documents, and rebuild local Chroma vector index.
- **Evaluation Suite Dashboard:** Interactive benchmark runner with latency, accuracy, and error analytics.
- **Dark / Light Theme:** Custom theme switcher with persistent local preference.

## Tech Stack

- **React 19** + **TypeScript**
- **Vite 8** (Build tooling & HMR)
- **Tailwind CSS v4**
- **Lucide React** (Icons)
- **React Markdown** & **Remark GFM** (Rich response rendering)

## Development

```bash
# Install dependencies
npm install

# Start development server on http://localhost:5173 (proxies /api to FastAPI on port 8000)
npm run dev

# Build for production (outputs to dist/)
npm run build
```
