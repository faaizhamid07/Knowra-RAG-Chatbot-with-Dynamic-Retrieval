import React from 'react';
import { Cpu, Sun, Moon, Bell } from 'lucide-react';

interface HeaderProps {
  selectedModel: string;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  selectedModel,
  theme,
  onToggleTheme,
}) => {
  return (
    <header className="h-[70px] bg-white dark:bg-[#0e0c0a] border-b border-[#e5e7eb] dark:border-[#221e1a] px-6 flex items-center justify-between z-10 select-none">
      {/* Model Badge */}
      <div className="flex items-center space-x-3">
        <div className="bg-[#f5f5f7] dark:bg-[#1a1715] border border-[#e5e7eb] dark:border-[#2f2b27] rounded-full h-11 px-4 flex items-center space-x-2.5">
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-[#009bff] to-[#ff882b] p-0.5 flex items-center justify-center">
            <div className="w-full h-full bg-white dark:bg-[#1a1715] rounded-full flex items-center justify-center">
              <Cpu className="w-3.5 h-3.5 text-[#ff882b]" />
            </div>
          </div>
          <span className="text-xs font-semibold text-[#161616] dark:text-[#f5f5f5] font-mono truncate max-w-[280px]">
            Model: {selectedModel}
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center space-x-3">
        {/* Theme Toggle Button */}
        <button
          onClick={onToggleTheme}
          className="w-10 h-10 rounded-full bg-[#f5f5f7] dark:bg-[#1a1715] border border-[#e5e7eb] dark:border-[#2f2b27] flex items-center justify-center text-[#4b5563] dark:text-[#d1d5db] hover:border-[#ff882b] hover:text-[#ff882b] transition-all cursor-pointer"
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
        >
          {theme === 'light' ? (
            <Sun className="w-4 h-4 text-[#ff882b]" />
          ) : (
            <Moon className="w-4 h-4 text-[#009bff]" />
          )}
        </button>

        {/* Notifications */}
        <button
          className="w-10 h-10 rounded-full bg-[#f5f5f7] dark:bg-[#1a1715] border border-[#e5e7eb] dark:border-[#2f2b27] flex items-center justify-center text-[#4b5563] dark:text-[#d1d5db] hover:text-[#0f172a] dark:hover:text-white transition-all cursor-pointer"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>

        {/* Header Avatar */}
        <div className="w-10 h-10 rounded-full bg-[#fbeae8] dark:bg-[#2c1514] text-[#a62925] dark:text-[#f87171] font-semibold text-sm flex items-center justify-center border border-[#f5b8b2] dark:border-[#521b18] shadow-sm">
          F
        </div>
      </div>
    </header>
  );
};
