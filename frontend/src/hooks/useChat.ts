import { useState, useEffect, useRef, useCallback } from 'react';
import {
  createConversation,
  deleteConversation as apiDeleteConversation,
  fetchConversations,
  fetchConversation,
  sendChatQueryStream,
  stopChatGeneration,
} from '../services/api';
import type { Conversation, Message, RetrievalMode } from '../types';

const STORAGE_ACTIVE_KEY = 'rag_active_conv_id';

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string>(() => {
    try {
      return localStorage.getItem(STORAGE_ACTIVE_KEY) || '';
    } catch {
      return '';
    }
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [currentMode, setCurrentMode] = useState<RetrievalMode | undefined>(undefined);
  const [inFlightSources, setInFlightSources] = useState<string[]>([]);

  // Selected configuration from sidebar
  const [selectedModel, setSelectedModel] = useState<string>('openai/gpt-oss-120b');
  const [forcedMode, setForcedMode] = useState<RetrievalMode>('dynamic');

  // Reference to track active generation task for Level B/C/D cancellation
  const activeGenerationIdRef = useRef<string | null>(null);

  // Sync activeId with localStorage
  useEffect(() => {
    try {
      if (activeId) {
        localStorage.setItem(STORAGE_ACTIVE_KEY, activeId);
      } else {
        localStorage.removeItem(STORAGE_ACTIVE_KEY);
      }
    } catch (e) {
      console.warn('localStorage access failed:', e);
    }
  }, [activeId]);

  // Load all conversations on mount
  const refreshConversations = useCallback(async () => {
    try {
      const list = await fetchConversations();
      setConversations(list);
      return list;
    } catch (err) {
      console.error('Failed to load conversations:', err);
      return [];
    }
  }, []);

  // Initial load: fetch conversations list and load messages for saved activeId if valid
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const list = await fetchConversations();
        if (!mounted) return;
        setConversations(list);

        const savedId = localStorage.getItem(STORAGE_ACTIVE_KEY);
        if (savedId && list.some((c) => c.id === savedId)) {
          setActiveId(savedId);
          const fullConv = await fetchConversation(savedId);
          if (mounted && fullConv && fullConv.messages) {
            setMessages(fullConv.messages);
          }
        } else if (list.length > 0) {
          // If savedId invalid but conversations exist, pick the most recent one
          const mostRecent = list[0];
          setActiveId(mostRecent.id);
          const fullConv = await fetchConversation(mostRecent.id);
          if (mounted && fullConv && fullConv.messages) {
            setMessages(fullConv.messages);
          }
        }
      } catch (err) {
        console.error('Error during initial conversation load:', err);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  // Create a new blank chat
  const handleNewChat = useCallback(async () => {
    try {
      const newConv = await createConversation('New Chat');
      setConversations((prev) => [newConv, ...prev.filter((c) => c.id !== newConv.id)]);
      setActiveId(newConv.id);
      setMessages([]);
      setInput('');
      setCurrentMode(undefined);
      setInFlightSources([]);
    } catch (err) {
      console.error('Failed to create new conversation:', err);
    }
  }, []);

  // Switch to an existing conversation
  const handleSelectConversation = useCallback(
    async (id: string) => {
      if (isGenerating || id === activeId) return; // Disallow switching during active generation
      setActiveId(id);
      setInput('');
      setCurrentMode(undefined);
      setInFlightSources([]);

      try {
        const fullConv = await fetchConversation(id);
        if (fullConv && fullConv.messages) {
          setMessages(fullConv.messages);
        } else {
          setMessages([]);
        }
      } catch (err) {
        console.error(`Failed to load messages for conversation ${id}:`, err);
        // Fallback to local copy if available
        const target = conversations.find((c) => c.id === id);
        setMessages(target?.messages || []);
      }
    },
    [conversations, isGenerating, activeId]
  );

  // Delete a conversation
  const handleDeleteConversation = useCallback(
    async (id: string) => {
      try {
        await apiDeleteConversation(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (activeId === id) {
          setActiveId('');
          setMessages([]);
          try {
            localStorage.removeItem(STORAGE_ACTIVE_KEY);
          } catch {}
        }
      } catch (err) {
        console.error('Failed to delete conversation:', err);
      }
    },
    [activeId]
  );

  // Send a message and stream the assistant response
  const handleSendMessage = useCallback(
    async (promptToSend?: string) => {
      const text = (promptToSend || input).trim();
      if (!text || isGenerating) return;

      let convId = activeId;
      // Auto-create conversation if none is active
      if (!convId) {
        try {
          const newConv = await createConversation('New Chat');
          convId = newConv.id;
          setActiveId(convId);
          setConversations((prev) => [newConv, ...prev]);
        } catch (err) {
          console.error('Failed to create conversation:', err);
          return;
        }
      }

      const userMessageId = `usr_${Date.now()}`;
      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const userMsg: Message = {
        id: userMessageId,
        role: 'user',
        content: text,
        time: nowStr,
      };

      const assistantMessageId = `ast_${Date.now()}`;
      const placeholderAssistantMsg: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        time: nowStr,
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, placeholderAssistantMsg]);
      setInput('');
      setIsGenerating(true);
      setCurrentMode(forcedMode);
      setInFlightSources([]);

      const historyForBackend = messages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map((m) => ({ role: m.role, content: m.content }));

      try {
        await sendChatQueryStream(
          {
            query: text,
            conversation_id: convId,
            selected_model: selectedModel,
            model: selectedModel,
            forced_mode: forcedMode,
            chat_history: historyForBackend,
          },
          {
            onStarted: (genId: string) => {
              activeGenerationIdRef.current = genId;
            },
            onRetrieval: (mode: RetrievalMode) => {
              setCurrentMode(mode);
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantMessageId ? { ...m, mode } : m))
              );
            },
            onSources: (sources: string[]) => {
              setInFlightSources(sources);
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantMessageId ? { ...m, sources } : m))
              );
            },
            onToken: (token: string) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId
                    ? { ...m, content: m.content + token, isStreaming: true }
                    : m
                )
              );
            },
            onCompleted: (finalAnswer: string, mode: RetrievalMode, sources?: string[]) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId
                    ? {
                        ...m,
                        content: finalAnswer,
                        mode,
                        sources,
                        isStreaming: false,
                        stopped: false,
                      }
                    : m
                )
              );
              setIsGenerating(false);
              activeGenerationIdRef.current = null;
              refreshConversations();
              setTimeout(() => {
                refreshConversations();
              }, 1500);
            },
            onStopped: (partialAnswer: string) => {
              // Preserve partial assistant output with stopped state marker
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId
                    ? {
                        ...m,
                        content: partialAnswer,
                        isStreaming: false,
                        stopped: true,
                      }
                    : m
                )
              );
              setIsGenerating(false);
              activeGenerationIdRef.current = null;
              refreshConversations();
              setTimeout(() => {
                refreshConversations();
              }, 1500);
            },
            onError: (errorMsg: string) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId
                    ? {
                        ...m,
                        content: errorMsg,
                        error: true,
                        mode: 'error',
                        isStreaming: false,
                      }
                    : m
                )
              );
              setIsGenerating(false);
              activeGenerationIdRef.current = null;
              refreshConversations();
            },
          }
        );
      } catch (err: any) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessageId
              ? {
                  ...m,
                  content: err.message || 'Error executing RAG stream',
                  error: true,
                  mode: 'error',
                  isStreaming: false,
                }
              : m
          )
        );
        setIsGenerating(false);
        activeGenerationIdRef.current = null;
        refreshConversations();
      }
    },
    [activeId, input, isGenerating, selectedModel, forcedMode, messages, refreshConversations]
  );

  // Real Level B/C/D Cancellation
  const handleStopGeneration = useCallback(async () => {
    if (!isGenerating || !activeId) return;

    try {
      await stopChatGeneration(activeId, activeGenerationIdRef.current || undefined);
    } catch (err) {
      console.error('Failed to trigger stop endpoint:', err);
    }
  }, [isGenerating, activeId]);

  const handleClearChat = useCallback(() => {
    handleNewChat();
  }, [handleNewChat]);

  return {
    conversations,
    activeId,
    messages,
    input,
    setInput,
    isGenerating,
    currentMode,
    inFlightSources,
    selectedModel,
    setSelectedModel,
    forcedMode,
    setForcedMode,
    handleNewChat,
    handleSelectConversation,
    handleDeleteConversation,
    handleSendMessage,
    handleStopGeneration,
    handleClearChat,
    refreshConversations,
  };
}
