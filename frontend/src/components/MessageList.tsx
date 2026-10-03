import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Brain,
  User,
  Globe,
  Database,
  Cpu,
  AlertCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Square,
  ExternalLink,
} from 'lucide-react';
import type { Message, RetrievalMode } from '../types';

interface MessageListProps {
  messages: Message[];
  isGenerating: boolean;
  currentMode?: RetrievalMode;
  inFlightSources?: string[];
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isGenerating,
  currentMode,
  inFlightSources,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleSources = (id: string) => {
    setExpandedSources((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const renderModeBadge = (mode?: RetrievalMode) => {
    switch (mode) {
      case 'web_search':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
            <Globe className="w-3 h-3" />
            <span>Web Search</span>
          </span>
        );
      case 'vectorstore':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
            <Database className="w-3 h-3" />
            <span>Vectorstore RAG</span>
          </span>
        );
      case 'llm_native':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <Cpu className="w-3 h-3" />
            <span>LLM Native</span>
          </span>
        );
      case 'error':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3 h-3" />
            <span>Error</span>
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
      {messages.map((msg) => {
        const isUser = msg.role === 'user';
        const isCopied = copiedId === msg.id;
        const hasSources = msg.sources && msg.sources.length > 0;
        const areSourcesExpanded = expandedSources[msg.id] ?? false;

        if (isUser) {
          return (
            <div key={msg.id} className="flex justify-end items-start space-x-3 max-w-3xl ml-auto">
              <div className="flex flex-col items-end space-y-1">
                <div className="bg-[#181615] text-white dark:bg-[#221e1a] border border-[#2e2a25] rounded-3xl rounded-tr-sm px-5 py-3.5 shadow-md max-w-xl text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                </div>
                {msg.time && (
                  <span className="text-[10px] text-[#888da8] px-2">{msg.time}</span>
                )}
              </div>
              <div className="w-8 h-8 rounded-full bg-[#fbeae8] dark:bg-[#2c1514] text-[#a62925] dark:text-[#f87171] font-semibold text-xs flex items-center justify-center border border-[#f5b8b2] dark:border-[#521b18] flex-shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            </div>
          );
        }

        return (
          <div key={msg.id} className="flex justify-start items-start space-x-3.5 max-w-3xl">
            {/* Assistant Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#009bff] to-[#ff882b] p-0.5 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
              <div className="w-full h-full bg-white dark:bg-[#141210] rounded-full flex items-center justify-center">
                <Brain className="w-4 h-4 text-[#ff882b]" />
              </div>
            </div>

            {/* Bubble & Metadata */}
            <div className="flex-1 space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-[#090909] dark:text-[#f5f5f5]">
                  Multi-Source Assistant
                </span>
                {renderModeBadge(msg.mode)}
                {msg.stopped && (
                  <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    <Square className="w-2.5 h-2.5" />
                    <span>Stopped</span>
                  </span>
                )}
              </div>

              {/* Message Content Body */}
              <div
                className={`bg-white dark:bg-[#161412] border border-[#e5e7eb] dark:border-[#26221e] rounded-3xl rounded-tl-sm p-5 shadow-sm text-sm text-[#161616] dark:text-[#f5f5f5] leading-relaxed relative ${
                  msg.isStreaming ? 'streaming-cursor' : ''
                }`}
              >
                {msg.error ? (
                  <div className="flex items-center space-x-2 text-rose-600 dark:text-rose-400 text-xs">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{msg.content}</span>
                  </div>
                ) : (
                  <div className="prose-chat">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content || (msg.isStreaming ? 'Thinking... 🤔' : '')}
                    </ReactMarkdown>
                  </div>
                )}

                {/* Sources Accordion */}
                {hasSources && (
                  <div className="mt-4 pt-3 border-t border-[#e5e7eb] dark:border-[#2b2723]">
                    <button
                      onClick={() => toggleSources(msg.id)}
                      className="flex items-center justify-between w-full text-xs font-medium text-[#64748b] dark:text-[#a1a1aa] hover:text-[#ff882b] transition-colors cursor-pointer"
                    >
                      <div className="flex items-center space-x-1.5">
                        <Globe className="w-3.5 h-3.5 text-[#009bff]" />
                        <span>Sources Referenced ({msg.sources?.length})</span>
                      </div>
                      {areSourcesExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {areSourcesExpanded && (
                      <div className="mt-2 space-y-1.5 pl-2">
                        {msg.sources?.map((src, sIdx) => (
                          <a
                            key={sIdx}
                            href={src}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center space-x-1.5 text-xs text-[#009bff] hover:underline truncate"
                          >
                            <ExternalLink className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{src}</span>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Message Bottom Toolbar */}
              <div className="flex items-center space-x-3 px-1 text-xs text-[#888da8]">
                {msg.time && <span>{msg.time}</span>}
                <button
                  onClick={() => handleCopy(msg.id, msg.content)}
                  className="flex items-center space-x-1 hover:text-[#0f172a] dark:hover:text-white transition-colors cursor-pointer"
                  title="Copy to clipboard"
                >
                  {isCopied ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-500" />
                      <span className="text-emerald-500 text-[10px]">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span className="text-[10px]">Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        );
      })}

      {/* In-Flight Status Indicator */}
      {isGenerating && (
        <div className="flex items-center space-x-2 text-xs text-[#888da8] pl-12">
          <div className="flex space-x-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[#009bff] animate-bounce" />
            <div className="w-1.5 h-1.5 rounded-full bg-[#ff882b] animate-bounce [animation-delay:0.2s]" />
            <div className="w-1.5 h-1.5 rounded-full bg-[#009bff] animate-bounce [animation-delay:0.4s]" />
          </div>
          <span>
            {currentMode ? `Retrieving via ${currentMode}...` : 'Routing query & retrieving context...'}
          </span>
          {inFlightSources && inFlightSources.length > 0 && (
            <span className="text-[10px] text-[#64748b]">
              ({inFlightSources.length} sources found)
            </span>
          )}
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
