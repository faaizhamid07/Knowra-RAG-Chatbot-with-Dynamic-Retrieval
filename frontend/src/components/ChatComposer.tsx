import React, { useEffect, useRef } from 'react';
import {
  Paperclip,
  MessageSquare,
  BarChart3,
  Mic,
  Send,
  Square,
  Trash2,
} from 'lucide-react';

interface ChatComposerProps {
  input: string;
  onInputChange: (val: string) => void;
  onSend: () => void;
  onStop: () => void;
  onClear: () => void;
  onOpenAttachment: () => void;
  onSwitchToEval: () => void;
  isGenerating: boolean;
}

export const ChatComposer: React.FC<ChatComposerProps> = ({
  input,
  onInputChange,
  onSend,
  onStop,
  onClear,
  onOpenAttachment,
  onSwitchToEval,
  isGenerating,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isGenerating && input.trim()) {
        onSend();
      }
    }
  };

  return (
    <div className="p-4 md:p-6 bg-transparent select-none">
      <div className="max-w-4xl mx-auto">
        {/* Signature Gradient Border Container */}
        <div className="p-[2px] rounded-[28px] bg-gradient-to-r from-[#a6d5ff] via-[#d0d3ff] to-[#ffc49d] shadow-lg shadow-[#009bff]/10">
          <div className="bg-white dark:bg-[#181614] rounded-[26px] p-4 flex flex-col justify-between transition-colors">
            {/* Input Field */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything..."
              rows={1}
              className="w-full bg-transparent border-none outline-none text-[#161616] dark:text-[#f5f5f5] placeholder-[#858ba6] dark:placeholder-[#71717a] text-sm md:text-base resize-none py-1 px-2 leading-relaxed"
            />

            {/* Bottom Actions Bar */}
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-[#f1f3f5] dark:border-[#221f1c]">
              {/* Left Slot: Attachment & Mode Pills */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={onOpenAttachment}
                  className="w-10 h-10 rounded-full bg-[#f5f5f7] dark:bg-[#221f1c] hover:bg-[#e9ecef] dark:hover:bg-[#2b2723] text-[#64748b] dark:text-[#d1d5db] flex items-center justify-center transition-colors"
                  title="Upload Document (.pdf, .txt)"
                >
                  <Paperclip className="w-4 h-4 text-[#009bff]" />
                </button>

                <div className="hidden sm:flex items-center space-x-1.5">
                  <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-[#f5f5f7] dark:bg-[#221f1c] text-[#161616] dark:text-[#f5f5f5] text-xs font-medium">
                    <MessageSquare className="w-3.5 h-3.5 text-[#009bff]" />
                    <span>Chat Mode</span>
                  </div>

                  <button
                    onClick={onSwitchToEval}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full hover:bg-[#f5f5f7] dark:hover:bg-[#221f1c] text-[#64748b] dark:text-[#a1a1aa] text-xs font-medium transition-colors"
                  >
                    <BarChart3 className="w-3.5 h-3.5" />
                    <span>Evaluation Mode</span>
                  </button>
                </div>

                <button
                  onClick={onClear}
                  className="p-2 rounded-full text-[#94a3b8] hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
                  title="Clear Chat / New Thread"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Right Slot: Voice & Dynamic Stop / Send Button */}
              <div className="flex items-center space-x-2.5">
                <button
                  className="p-2 rounded-full text-[#94a3b8] dark:text-[#71717a] hover:text-[#0f172a] dark:hover:text-white transition-colors"
                  title="Voice Input (mock)"
                >
                  <Mic className="w-4 h-4" />
                </button>

                {isGenerating ? (
                  <button
                    onClick={onStop}
                    className="h-10 px-4 rounded-2xl bg-rose-600 hover:bg-rose-700 text-white flex items-center space-x-2 text-xs font-semibold shadow-md shadow-rose-600/20 transition-all hover:scale-105 active:scale-95"
                    title="Stop Generation (Cancel socket & provider stream)"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={onSend}
                    disabled={!input.trim()}
                    className={`h-10 w-10 rounded-2xl flex items-center justify-center transition-all ${
                      input.trim()
                        ? 'bg-gradient-to-r from-[#009bff] to-[#ff882b] text-white shadow-md shadow-[#ff882b]/20 hover:scale-105 active:scale-95 cursor-pointer'
                        : 'bg-[#e2e8f0] dark:bg-[#2a2622] text-[#94a3b8] dark:text-[#524d47] cursor-not-allowed'
                    }`}
                    title="Send Prompt (Enter)"
                  >
                    <Send className="w-4 h-4 ml-0.5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
