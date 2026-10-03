import type {
  BenchmarkQuestion,
  Conversation,
  DocumentStatus,
  EvalResponse,
  Message,
  SystemStatus,
} from '../types';

const API_BASE = '/api';

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error('Failed to fetch system status');
  return res.json();
}

export async function fetchModels(): Promise<{ models: string[]; default: string }> {
  const res = await fetch(`${API_BASE}/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function fetchConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE}/conversations`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  const data = await res.json();
  return data.conversations || [];
}

export async function fetchConversation(id: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  if (!res.ok) throw new Error('Failed to fetch conversation');
  return res.json();
}

export async function createConversation(title?: string, id?: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, title }),
  });
  if (!res.ok) throw new Error('Failed to create conversation');
  return res.json();
}

export async function updateConversation(
  id: string,
  data: { title?: string; messages?: Message[] }
): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update conversation');
  return res.json();
}

export async function deleteConversation(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete conversation');
  const data = await res.json();
  return data.success;
}

export async function stopChatGeneration(
  conversationId: string,
  generationId?: string
): Promise<{ stopped: boolean; status?: string; reason?: string }> {
  const res = await fetch(`${API_BASE}/chat/${conversationId}/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ generation_id: generationId }),
  });
  if (!res.ok && res.status !== 404) {
    throw new Error('Failed to stop generation');
  }
  return res.json();
}

export async function fetchDocuments(): Promise<DocumentStatus> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocuments(
  files: FileList | File[]
): Promise<{ uploaded: string[]; errors: string[]; total_uploaded: number }> {
  const formData = new FormData();
  Array.from(files).forEach((f) => formData.append('files', f));
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Failed to upload documents');
  const data = await res.json();
  return {
    uploaded: data.uploaded || [],
    errors: data.errors || [],
    total_uploaded: (data.uploaded || []).length,
  };
}

export async function deleteAllDocuments(): Promise<{ deleted_count: number; failed_files: string[] }> {
  const res = await fetch(`${API_BASE}/documents/delete-all`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete all documents');
  return res.json();
}

export async function deleteDocument(filename: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
  return true;
}

export async function rebuildVectorstore(): Promise<{
  success: boolean;
  chunks: number;
  docs: number;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/vectorstore/rebuild`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to rebuild vectorstore' }));
    throw new Error(err.detail || 'Failed to rebuild vectorstore');
  }
  return res.json();
}

export async function deleteVectorstore(): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/vectorstore/delete`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete vectorstore');
  return res.json();
}

export async function fetchBenchmarkQuestions(): Promise<{
  questions: BenchmarkQuestion[];
  count: number;
}> {
  const res = await fetch(`${API_BASE}/evaluate/questions`);
  if (!res.ok) throw new Error('Failed to fetch benchmark questions');
  return res.json();
}

export async function runEvaluationSuite(options: {
  num_questions?: number;
  model?: string;
}): Promise<EvalResponse> {
  const res = await fetch(`${API_BASE}/evaluate/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      num_questions: options.num_questions ?? 5,
      model: options.model,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to run evaluation' }));
    throw new Error(err.detail || 'Failed to run evaluation');
  }
  return res.json();
}

export async function fetchEnvTemplate(): Promise<string> {
  const res = await fetch(`${API_BASE}/env/template`);
  if (!res.ok) throw new Error('Failed to fetch .env template');
  return res.text();
}

export interface StreamCallbacks {
  onStarted?: (generationId: string) => void;
  onRetrieval?: (mode: any) => void;
  onSources?: (sources: string[]) => void;
  onToken?: (token: string) => void;
  onCompleted?: (finalAnswer: string, mode: any, sources?: string[]) => void;
  onStopped?: (partialAnswer: string) => void;
  onError?: (errorMsg: string) => void;
}

export async function sendChatQueryStream(
  params: {
    query: string;
    conversation_id: string;
    selected_model?: string;
    model?: string;
    forced_mode?: string | null;
    chat_history?: Array<{ role: string; content: string }>;
  },
  callbacks: StreamCallbacks
): Promise<void> {
  const modelToUse = params.model || params.selected_model;
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: params.query,
      conversation_id: params.conversation_id,
      model: modelToUse,
      selected_model: modelToUse,
      forced_mode: params.forced_mode === 'dynamic' ? null : params.forced_mode,
      chat_history: params.chat_history || [],
    }),
  });

  if (!res.ok) {
    if (res.status === 409) {
      throw new Error(
        'A generation is already active for this conversation. Please wait or stop it first.'
      );
    }
    const err = await res.json().catch(() => ({ detail: 'Failed to start chat generation' }));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }

  if (!res.body) {
    throw new Error('No response body returned from chat stream.');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent: string | null = null;
      let currentData: string | null = null;

      let isTerminal = false;
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          if (currentEvent && currentData) {
            try {
              const parsed = JSON.parse(currentData);
              switch (currentEvent) {
                case 'started':
                  callbacks.onStarted?.(parsed.generation_id);
                  break;
                case 'retrieval':
                  callbacks.onRetrieval?.(parsed.retrieval_mode);
                  break;
                case 'sources':
                  callbacks.onSources?.(parsed.sources || []);
                  break;
                case 'token':
                  callbacks.onToken?.(parsed.delta || '');
                  break;
                case 'completed':
                  callbacks.onCompleted?.(
                    parsed.answer,
                    parsed.retrieval_mode,
                    parsed.sources
                  );
                  isTerminal = true;
                  break;
                case 'stopped':
                  callbacks.onStopped?.(parsed.partial);
                  isTerminal = true;
                  break;
                case 'error':
                  callbacks.onError?.(parsed.message);
                  isTerminal = true;
                  break;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e, currentData);
            }
          }
          currentEvent = null;
          currentData = null;
          if (isTerminal) break;
          continue;
        }

        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.slice(6).trim();
        } else if (trimmed.startsWith('data:')) {
          currentData = trimmed.slice(5).trim();
        }
      }

      if (isTerminal) {
        try {
          await reader.cancel();
        } catch {}
        break;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
