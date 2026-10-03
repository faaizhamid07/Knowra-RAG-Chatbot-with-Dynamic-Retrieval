import React, { useState } from 'react';
import {
  MessageSquare,
  Plus,
  Search,
  Trash2,
  ChevronRight,
  Clock,
  X,
} from 'lucide-react';
import type { Conversation } from '../types';

interface ChatHistoryPanelProps {
  conversations: Conversation[];
  activeId: string;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onNewChat: () => void;
  onClose?: () => void;
}

export const ChatHistoryPanel: React.FC<ChatHistoryPanelProps> = ({
  conversations,
  activeId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatTimestamp = (ts: number) => {
    const d = new Date(ts * 1000);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  return (
    <aside className="w-[340px] flex-shrink-0 bg-[#fff3e9]/50 dark:bg-[#120f0d] border border-[#f0e4d8] dark:border-[#292521] rounded-3xl shadow-sm flex flex-col justify-between p-5 h-full overflow-y-auto select-none">
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MessageSquare className="w-4 h-4 text-[#ff882b]" />
            <h2 className="font-semibold text-base text-[#111] dark:text-[#f5f5f5]">
              Chat History
            </h2>
          </div>

          <button
            onClick={onNewChat}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white dark:bg-[#1c1a18] border border-[#e5e7eb] dark:border-[#363333] hover:border-[#ff882b] text-xs font-medium text-[#161616] dark:text-[#f5f5f5] transition-all shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-[#ff882b]" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <div className="bg-white dark:bg-[#1a1715] border border-[#e4e5ec] dark:border-[#2a2622] rounded-2xl h-10 px-3.5 flex items-center justify-between text-xs text-[#888da8] focus-within:border-[#ff882b] transition-colors shadow-sm">
            <div className="flex items-center space-x-2 flex-1 mr-2">
              <Search className="w-3.5 h-3.5 text-[#888da8] flex-shrink-0" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search chats..."
                className="bg-transparent border-none outline-none text-xs text-[#161616] dark:text-[#f5f5f5] placeholder-[#888da8] w-full"
              />
            </div>
            {searchTerm ? (
              <button
                onClick={() => setSearchTerm('')}
                className="p-1 rounded-md text-[#888da8] hover:text-[#111] dark:hover:text-white hover:bg-[#f1f5f9] dark:hover:bg-[#25221f] transition-colors cursor-pointer"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            ) : (
              <span className="text-[#94a3b8] dark:text-[#52525b] text-[10px] font-mono">
                /
              </span>
            )}
          </div>
        </div>

        {/* Conversation List */}
        <div className="space-y-2">
          {filtered.length === 0 ? (
            <div className="text-center py-12 px-4">
              <Clock className="w-8 h-8 text-[#cbd5e1] dark:text-[#38332c] mx-auto mb-2" />
              <p className="text-xs font-medium text-[#888da8]">No conversations yet</p>
              <p className="text-[11px] text-[#a1a1aa] mt-1">
                Start a new chat to begin prompting the RAG engine.
              </p>
            </div>
          ) : (
            filtered.map((conv) => {
              const isActive = conv.id === activeId;
              return (
                <div
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`group relative flex items-center justify-between p-3 rounded-2xl border cursor-pointer transition-all ${
                    isActive
                      ? 'bg-white dark:bg-[#1c1a18] border-[#009bff]/50 dark:border-[#009bff]/40 shadow-sm'
                      : 'bg-white/60 dark:bg-[#161412]/60 border-transparent hover:bg-white dark:hover:bg-[#1c1a18] hover:border-[#e5e7eb] dark:hover:border-[#2a2622]'
                  }`}
                >
                  {/* Left content */}
                  <div className="flex items-start space-x-2.5 overflow-hidden pr-2">
                    <div
                      className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                        isActive ? 'bg-[#ff882b]' : 'bg-transparent'
                      }`}
                    />
                    <div className="overflow-hidden">
                      <p className="text-xs font-medium text-[#111] dark:text-[#f5f5f5] truncate">
                        {conv.title || 'Untitled Chat'}
                      </p>
                      <p className="text-[10px] text-[#888da8] mt-0.5 flex items-center space-x-1">
                        <span>{formatTimestamp(conv.updated_at || conv.created_at)}</span>
                        {conv.message_count !== undefined && conv.message_count > 0 && (
                          <span>• {conv.message_count} msgs</span>
                        )}
                      </p>
                    </div>
                  </div>

                  {/* Right actions */}
                  <div className="flex items-center space-x-1 flex-shrink-0">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-[#a1a1aa] hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-all cursor-pointer"
                      title="Delete Conversation"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                    <ChevronRight className="w-3.5 h-3.5 text-[#cbd5e1] dark:text-[#423d38] group-hover:text-[#ff882b] transition-colors" />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-[#f0e4d8] dark:border-[#292521] text-center">
        <p className="text-[11px] text-[#888da8]">
          {conversations.length} saved thread{conversations.length === 1 ? '' : 's'}
        </p>
      </div>
    </aside>
  );
};
