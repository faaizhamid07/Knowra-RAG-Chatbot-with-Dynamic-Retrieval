import React from 'react';
import { PanelLeft, ChevronRight } from 'lucide-react';

interface WindowToolbarProps {
  onToggleSidebar?: () => void;
  onToggleHistory?: () => void;
  sidebarOpen: boolean;
  historyOpen: boolean;
}

export const WindowToolbar: React.FC<WindowToolbarProps> = ({
  onToggleSidebar,
  onToggleHistory,
  sidebarOpen,
  historyOpen,
}) => {
  return (
    <header className="h-[52px] bg-[#fcfdfe] dark:bg-[#0c0a08] border-b border-[#e2e8f0] dark:border-[#201c18] px-5 flex items-center justify-between select-none z-20">
      {/* Left Toolbar Items */}
      <div className="flex items-center space-x-2">
        {/* Sidebar Toggle */}
        <button
          onClick={onToggleSidebar}
          className={`p-1.5 rounded-lg border transition-colors ${
            sidebarOpen
              ? 'bg-[#f1f5f9] dark:bg-[#1e1b18] border-[#cbd5e1] dark:border-[#38332c] text-[#0f172a] dark:text-[#f8fafc]'
              : 'border-transparent text-[#64748b] dark:text-[#94a3b8] hover:bg-[#f1f5f9] dark:hover:bg-[#1e1b18]'
          }`}
          title="Toggle Sidebar"
        >
          <PanelLeft className="w-4 h-4" />
        </button>

        {/* Breadcrumb / Title */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs text-[#64748b] dark:text-[#a1a1aa] ml-2 font-medium">
          <span>Knowra</span>
          <ChevronRight className="w-3.5 h-3.5 text-[#94a3b8] dark:text-[#52525b]" />
          <span className="text-[#0f172a] dark:text-[#f4f4f5] font-semibold">Ask. Retrieve. Understand.</span>
        </div>
      </div>

      {/* Center status indicator */}
      <div className="flex items-center space-x-2 text-xs text-[#64748b] dark:text-[#a1a1aa]">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span className="hidden md:inline font-mono">FastAPI + LangGraph + React</span>
      </div>

      {/* Right toggle button */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onToggleHistory}
          className={`text-xs px-2.5 py-1 rounded-md border font-medium transition-colors ${
            historyOpen
              ? 'bg-[#f1f5f9] dark:bg-[#1e1b18] border-[#cbd5e1] dark:border-[#38332c] text-[#0f172a] dark:text-[#f8fafc]'
              : 'border-transparent text-[#64748b] dark:text-[#94a3b8] hover:bg-[#f1f5f9] dark:hover:bg-[#1e1b18]'
          }`}
        >
          History Panel
        </button>
      </div>
    </header>
  );
};
