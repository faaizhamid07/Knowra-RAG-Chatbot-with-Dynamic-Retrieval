import React, { useState } from 'react';
import {
  Brain,
  Plus,
  Search,
  Settings,
  Database,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  MoreVertical,
  Layers,
  X,
} from 'lucide-react';
import type { RetrievalMode, SystemStatus } from '../types';

export const AVAILABLE_GROQ_MODELS = [
  'openai/gpt-oss-120b',
  'openai/gpt-oss-20b',
  'qwen/qwen3.8-27b',
  'allam-2-7b',
  'llama-3.3-70b-versatile',
  'deepseek-r1-distill-qwen-32b',
  'meta-llama/llama-4-scout-17b-16e-instruct',
  'meta-llama/llama-4-maverick-17b-128e-instruct',
];

interface SidebarProps {
  selectedModel: string;
  onSelectModel: (model: string) => void;
  forcedMode: RetrievalMode;
  onSelectForcedMode: (mode: RetrievalMode) => void;
  onOpenDataModal: () => void;
  isDataModalOpen?: boolean;
  status: SystemStatus | null;
  onNewChat?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  selectedModel,
  onSelectModel,
  forcedMode,
  onSelectForcedMode,
  onOpenDataModal,
  isDataModalOpen = false,
  status,
  onNewChat,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Automatically sync activeTab with modal state: when modal closes, highlight returns to 'chat'
  const activeTab = isDataModalOpen ? 'data' : 'chat';

  const allEnvConfigured =
    status?.configured.groq_api_key &&
    status?.configured.tavily_api_key;

  return (
    <aside className="w-[360px] flex-shrink-0 bg-white dark:bg-[#090604] border border-[#e5e7eb] dark:border-[#292521] rounded-3xl shadow-sm text-[#161616] dark:text-[#f5f5f5] flex flex-col justify-between p-5 h-full overflow-y-auto select-none transition-colors">
      <div className="space-y-6">
        {/* Brand Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#009bff] to-[#ff882b] flex items-center justify-center p-0.5 shadow-lg shadow-[#009bff]/20">
              <div className="w-full h-full bg-white dark:bg-[#090604] rounded-[14px] flex items-center justify-center">
                <Brain className="w-5 h-5 text-[#ff882b]" />
              </div>
            </div>
            <div>
              <h1 className="font-semibold text-lg tracking-tight text-[#161616] dark:text-white">Knowra</h1>
              <p className="text-xs text-[#64748b] dark:text-[#a1a1aa]">Ask. Retrieve. Understand.</p>
            </div>
          </div>

          {onNewChat && (
            <button
              onClick={onNewChat}
              className="w-9 h-9 rounded-xl bg-[#f5f5f7] dark:bg-[#1d1b1a] border border-[#e5e7eb] dark:border-[#363333] hover:border-[#ff882b] hover:text-[#ff882b] flex items-center justify-center text-[#64748b] dark:text-[#d3d2d4] transition-all cursor-pointer shadow-sm"
              title="Start New Chat"
            >
              <Plus className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Search Bar / Quick Action */}
        <div className="relative">
          <div className="bg-[#f5f5f7] dark:bg-[#1d1b1a] border border-[#e5e7eb] dark:border-[#2a2928] rounded-2xl h-11 px-3.5 flex items-center justify-between text-sm text-[#161616] dark:text-[#d3d2d4] focus-within:border-[#009bff] transition-colors">
            <div className="flex items-center space-x-2.5 flex-1 mr-2">
              <Search className="w-4 h-4 text-[#888da8] flex-shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="bg-transparent border-none outline-none text-sm text-[#161616] dark:text-[#f5f5f5] placeholder-[#858ba6] dark:placeholder-[#71717a] w-full"
              />
            </div>
            {searchQuery ? (
              <button
                onClick={() => setSearchQuery('')}
                className="p-1 rounded-md text-[#888da8] hover:text-[#161616] dark:hover:text-white hover:bg-[#e5e7eb] dark:hover:bg-[#2a2928] transition-colors cursor-pointer"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            ) : (
              <span className="text-[#94a3b8] dark:text-[#52525b] text-xs font-mono">
                /
              </span>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="space-y-2">
          <button
            className={`w-full h-12 px-4 rounded-2xl flex items-center space-x-3 text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'chat'
                ? 'bg-gradient-to-r from-[#009bff] to-[#ff882b] text-white shadow-md shadow-[#009bff]/20'
                : 'bg-[#f5f5f7] dark:bg-[#181615] text-[#64748b] dark:text-[#d3d2d4] hover:bg-[#e9ecef] dark:hover:bg-[#201d1c]'
            }`}
          >
            <Settings className="w-4 h-4" />
            <span>Chat Configuration</span>
          </button>

          <button
            onClick={onOpenDataModal}
            className={`w-full h-12 px-4 rounded-2xl flex items-center justify-between text-sm font-medium transition-all cursor-pointer ${
              activeTab === 'data'
                ? 'bg-gradient-to-r from-[#009bff] to-[#ff882b] text-white shadow-md'
                : 'bg-[#f5f5f7] dark:bg-[#181615] text-[#64748b] dark:text-[#d3d2d4] hover:bg-[#e9ecef] dark:hover:bg-[#201d1c]'
            }`}
          >
            <div className="flex items-center space-x-3">
              <Database className="w-4 h-4" />
              <span>Data Management</span>
            </div>
            {status?.vectorstore_present && (
              <span className="w-2 h-2 rounded-full bg-emerald-400" title="ChromaDB Active" />
            )}
          </button>
        </div>

        <div className="h-[1px] bg-[#e5e7eb] dark:bg-[#292521]" />

        {/* Environment Status Card */}
        <div className="space-y-2">
          <h2 className="text-xs uppercase tracking-wider font-semibold text-[#64748b] dark:text-[#a1a1aa]">
            Environment Configuration
          </h2>
          <div
            className={`p-3.5 rounded-2xl border flex items-start space-x-3 transition-colors ${
              allEnvConfigured
                ? 'bg-[#edfbf2] dark:bg-[#081b0c] border-[#a3e6be] dark:border-[#155d28] text-[#0d7d3c] dark:text-[#22e877]'
                : 'bg-[#fef9ee] dark:bg-[#1f1609] border-[#fed7aa] dark:border-[#5d3e15] text-[#b45309] dark:text-[#f59e0b]'
            }`}
          >
            <div className="mt-0.5">
              {allEnvConfigured ? (
                <CheckCircle2 className="w-4 h-4 text-[#16a34a] dark:text-[#21cd74]" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-[#d97706] dark:text-[#f59e0b]" />
              )}
            </div>
            <div className="text-xs leading-relaxed">
              <p className="font-medium text-[#161616] dark:text-white">
                {allEnvConfigured ? 'API Credentials Active' : 'Missing Credentials'}
              </p>
              <p className="text-[#64748b] dark:text-[#a1a1aa] mt-0.5">
                {allEnvConfigured
                  ? 'Groq & Tavily are ready for dynamic retrieval.'
                  : 'Check server .env for GROQ_API_KEY & TAVILY_API_KEY.'}
              </p>
            </div>
          </div>
        </div>

        {/* Model Settings */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs uppercase tracking-wider font-semibold text-[#64748b] dark:text-[#a1a1aa]">
              Model Settings
            </h2>
            <span className="text-[10px] text-[#ff882b] bg-[#ff882b]/10 px-2 py-0.5 rounded-full font-mono">
              Groq Cloud
            </span>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-[#64748b] dark:text-[#d3d2d4] font-medium">LLM Model:</label>
            <div className="relative">
              <select
                value={selectedModel}
                onChange={(e) => onSelectModel(e.target.value)}
                className="w-full bg-[#f5f5f7] dark:bg-[#1c1a18] border border-[#e5e7eb] dark:border-[#363333] hover:border-[#cbd5e1] dark:hover:border-[#4d4845] focus:border-[#009bff] rounded-2xl py-2.5 px-3.5 text-xs text-[#161616] dark:text-white appearance-none outline-none cursor-pointer transition-colors"
              >
                {AVAILABLE_GROQ_MODELS.map((m) => (
                  <option key={m} value={m} className="bg-white dark:bg-[#1c1a18] text-[#161616] dark:text-white">
                    {m}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-[#888da8] absolute right-3.5 top-3 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Retrieval Mode Radios */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs uppercase tracking-wider font-semibold text-[#64748b] dark:text-[#a1a1aa]">
              Retrieval Mode:
            </h2>
            <Layers className="w-3.5 h-3.5 text-[#888da8]" />
          </div>

          <div className="space-y-2">
            {[
              { id: 'dynamic', label: 'Dynamic (Default)', desc: 'AI Router chooses best path' },
              { id: 'llm_native', label: 'LLM Native Only', desc: 'Direct model knowledge only' },
              { id: 'vectorstore', label: 'Vectorstore Only', desc: 'ChromaDB documents (MMR k=7)' },
              { id: 'web_search', label: 'Web Search Only', desc: 'Live Tavily web retrieval' },
            ].map((mode) => {
              const isSelected = forcedMode === mode.id;
              return (
                <label
                  key={mode.id}
                  onClick={() => onSelectForcedMode(mode.id as RetrievalMode)}
                  className={`flex items-start space-x-3 p-2.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#f0f7ff] dark:bg-[#1d1b1a] border-[#009bff] dark:border-[#009bff]/50 text-[#161616] dark:text-white'
                      : 'bg-transparent border-[#e5e7eb] dark:border-[#23201d] text-[#64748b] dark:text-[#a1a1aa] hover:bg-[#f8fafc] dark:hover:bg-[#141210] hover:text-[#0f172a] dark:hover:text-[#d3d2d4]'
                  }`}
                >
                  <div className="mt-0.5 flex items-center justify-center w-4 h-4 rounded-full border border-[#cbd5e1] dark:border-[#4d4845]">
                    {isSelected && (
                      <div className="w-2 h-2 rounded-full bg-gradient-to-r from-[#009bff] to-[#ff882b]" />
                    )}
                  </div>
                  <div className="text-xs">
                    <span className="font-medium text-[#161616] dark:text-white block">{mode.label}</span>
                    <span className="text-[11px] text-[#858ba6] dark:text-[#71717a]">{mode.desc}</span>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      </div>

      {/* User Account Footer */}
      <div className="pt-4 border-t border-[#e5e7eb] dark:border-[#292521]">
        <div className="flex items-center justify-between p-2 rounded-2xl bg-[#f8fafc] dark:bg-[#141210] border border-[#e5e7eb] dark:border-[#23201d]">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-[#fbeae8] dark:bg-[#2c1514] text-[#a62925] dark:text-[#f87171] font-semibold text-sm flex items-center justify-center border border-[#f5b8b2] dark:border-[#521b18]">
              F
            </div>
            <div>
              <p className="text-xs font-semibold text-[#161616] dark:text-white">Faaiz Hamid</p>
              <p className="text-[10px] text-[#64748b] dark:text-[#71717a]">Administrator</p>
            </div>
          </div>
          <button className="p-1 text-[#64748b] dark:text-[#71717a] hover:text-[#0f172a] dark:hover:text-white transition-colors cursor-pointer">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
