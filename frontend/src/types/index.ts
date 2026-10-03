export type RetrievalMode = 'dynamic' | 'llm_native' | 'vectorstore' | 'web_search' | 'error' | 'unknown';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  mode?: RetrievalMode;
  time?: string;
  sources?: string[];
  stopped?: boolean;
  error?: boolean;
  isStreaming?: boolean;
  generationId?: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  message_count?: number;
  last_message?: string;
  messages?: Message[];
}

export interface SystemStatus {
  configured: {
    groq_api_key: boolean;
    tavily_api_key: boolean;
    langchain_api_key: boolean;
  };
  model: string;
  embedding_model: string;
  web_search_provider: string;
  vectorstore_present: boolean;
  data_files_count: number;
  active_generations: Array<{ conversation_id: string; generation_id: string; status: string }>;
}

export interface DocumentFile {
  name: string;
  size_bytes: number;
  size_formatted: string;
  modified_at: number;
}

export interface DocumentStatus {
  files: DocumentFile[];
  count: number;
  vectorstore_exists: boolean;
  chroma_path: string;
}

export interface BenchmarkQuestion {
  question_id: number;
  question: string;
  expected_mode?: string;
  expected_answer_keywords?: string;
}

export interface EvalResultRow {
  question_id: number;
  question: string;
  expected_mode: string | null;
  actual_mode: string;
  mode_correct: boolean | null;
  answer: string;
  latency_seconds: number;
  sources_used: string | null;
  error: string | null;
}

export interface EvalSummary {
  total_questions: number;
  successful_runs: number;
  error_rate_pct: number;
  mode_accuracy_pct: number;
  avg_latency_seconds: number;
  model_used: string;
}

export interface EvalResponse {
  summary: EvalSummary;
  results: EvalResultRow[];
}
