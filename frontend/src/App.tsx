import { useState, useEffect } from 'react';
import { WindowToolbar } from './components/WindowToolbar';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { EmptyChatHero } from './components/EmptyChatHero';
import { MessageList } from './components/MessageList';
import { ChatComposer } from './components/ChatComposer';
import { ChatHistoryPanel } from './components/ChatHistoryPanel';
import { DataManagementModal } from './components/DataManagementModal';
import { EvaluationView } from './components/EvaluationView';
import { useChat } from './hooks/useChat';
import { fetchSystemStatus } from './services/api';
import type { SystemStatus } from './types';

export function App() {
  // Theme state with localStorage persistence, default to 'dark'
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    try {
      const saved = localStorage.getItem('rag_theme');
      if (saved === 'light' || saved === 'dark') return saved;
    } catch {}
    return 'dark';
  });

  const [appMode, setAppMode] = useState<'chat' | 'evaluation'>('chat');

  // Sidebar & Panel toggles
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [isDataModalOpen, setIsDataModalOpen] = useState(false);

  // System status state
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  // Custom chat hook
  const {
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
  } = useChat();

  // Fetch system status on load
  const loadStatus = async () => {
    try {
      const data = await fetchSystemStatus();
      setSystemStatus(data);
    } catch (e) {
      console.error('Failed to load system status:', e);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  // Sync theme with HTML root class and localStorage
  useEffect(() => {
    try {
      localStorage.setItem('rag_theme', theme);
    } catch (e) {
      console.warn('Failed to save theme in localStorage:', e);
    }
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#faf8f5] dark:bg-[#080401] text-[#161616] dark:text-[#f5f5f5] overflow-hidden font-sans transition-colors duration-200">
      {/* 1. macOS Style Window Toolbar */}
      <WindowToolbar
        sidebarOpen={isSidebarOpen}
        historyOpen={isHistoryOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        onToggleHistory={() => setIsHistoryOpen((prev) => !prev)}
      />

      {/* 2. Main Content Canvas with Gutters & Rounded Panels */}
      <div className="flex-1 flex overflow-hidden p-3 gap-3 bg-[#faf8f5] dark:bg-[#080401]">
        {/* Left Navigation Sidebar */}
        {isSidebarOpen && (
          <Sidebar
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            forcedMode={forcedMode}
            onSelectForcedMode={setForcedMode}
            onOpenDataModal={() => setIsDataModalOpen(true)}
            isDataModalOpen={isDataModalOpen}
            status={systemStatus}
            onNewChat={handleNewChat}
          />
        )}

        {/* Center Main Workspace */}
        <main className="flex-1 flex flex-col h-full overflow-hidden bg-white/70 dark:bg-[#100e0c]/70 backdrop-blur-md relative border border-[#e5e7eb] dark:border-[#201d1a] rounded-3xl shadow-sm">
          {/* Header Bar */}
          <Header
            selectedModel={selectedModel}
            theme={theme}
            onToggleTheme={toggleTheme}
          />

          {/* Dynamic Content Area */}
          {appMode === 'evaluation' ? (
            <EvaluationView onBack={() => setAppMode('chat')} />
          ) : (
            <div className="flex-1 flex flex-col h-full overflow-hidden">
              {/* Message Stream or Empty Hero */}
              {messages.length === 0 ? (
                <EmptyChatHero onSelectSuggestion={(prompt) => handleSendMessage(prompt)} />
              ) : (
                <MessageList
                  messages={messages}
                  isGenerating={isGenerating}
                  currentMode={currentMode}
                  inFlightSources={inFlightSources}
                />
              )}

              {/* Chat Composer */}
              <ChatComposer
                input={input}
                onInputChange={setInput}
                onSend={() => handleSendMessage()}
                onStop={handleStopGeneration}
                onClear={handleClearChat}
                onOpenAttachment={() => setIsDataModalOpen(true)}
                onSwitchToEval={() => setAppMode('evaluation')}
                isGenerating={isGenerating}
              />
            </div>
          )}
        </main>

        {/* Right Chat History Panel */}
        {isHistoryOpen && appMode === 'chat' && (
          <ChatHistoryPanel
            conversations={conversations}
            activeId={activeId}
            onSelectConversation={handleSelectConversation}
            onDeleteConversation={handleDeleteConversation}
            onNewChat={handleNewChat}
          />
        )}
      </div>

      {/* Document & Vectorstore Management Modal */}
      <DataManagementModal
        isOpen={isDataModalOpen}
        onClose={() => setIsDataModalOpen(false)}
        onStatusChange={loadStatus}
      />
    </div>
  );
}

export default App;
