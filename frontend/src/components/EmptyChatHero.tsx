import React from 'react';
import { Brain, FileText, Globe, BarChart2, Lightbulb } from 'lucide-react';

interface EmptyChatHeroProps {
  onSelectSuggestion: (prompt: string) => void;
}

export const EmptyChatHero: React.FC<EmptyChatHeroProps> = ({ onSelectSuggestion }) => {
  const suggestions = [
    {
      title: 'Summarize Documents',
      subtitle: 'Get key insights from your uploaded files',
      icon: FileText,
      iconBg: 'bg-[#e1f1ff] dark:bg-[#152e4d]',
      iconColor: 'text-[#009bff]',
      prompt: 'Summarize the core technical findings and concepts in the uploaded AI papers and documentation.',
    },
    {
      title: 'Search the Web',
      subtitle: 'Find latest information from across the internet',
      icon: Globe,
      iconBg: 'bg-[#f0ecff] dark:bg-[#2d1b4e]',
      iconColor: 'text-[#8b5cf6]',
      prompt: 'What are the latest updates, benchmark results, and releases in AI and LLM research today?',
    },
    {
      title: 'Compare Data',
      subtitle: 'Analyze and compare information from multiple sources',
      icon: BarChart2,
      iconBg: 'bg-[#dff9eb] dark:bg-[#123824]',
      iconColor: 'text-[#10b981]',
      prompt: 'Compare the Transformer architecture with Mamba and State Space Models (SSMs) across latency and memory scaling.',
    },
    {
      title: 'Extract Insights',
      subtitle: 'Get key facts and technical insights from documents',
      icon: Lightbulb,
      iconBg: 'bg-[#fff0e4] dark:bg-[#43230c]',
      iconColor: 'text-[#ff882b]',
      prompt: 'Explain how Multi-Head Attention works under the hood with Query, Key, and Value vector projections.',
    },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-4xl mx-auto select-none">
      {/* Halo & Brain Logo */}
      <div className="relative mb-6 flex items-center justify-center">
        {/* Glow halo */}
        <div className="absolute w-36 h-36 rounded-full bg-gradient-to-r from-[#009bff]/20 to-[#ff882b]/25 blur-2xl pointer-events-none" />

        {/* Circuit circle background */}
        <div className="w-24 h-24 rounded-3xl bg-white dark:bg-[#181614] border border-[#e2e8f0] dark:border-[#2b2723] p-1 shadow-xl flex items-center justify-center">
          <div className="w-full h-full rounded-2xl bg-gradient-to-tr from-[#009bff]/10 to-[#ff882b]/15 flex items-center justify-center">
            <Brain className="w-12 h-12 text-[#ff882b] drop-shadow-md" />
          </div>
        </div>
      </div>

      {/* Heading */}
      <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-[#090909] dark:text-[#f5f5f5] mb-3">
        Knowra
      </h1>
      <p className="text-sm md:text-base text-[#666b7d] dark:text-[#a1a1aa] max-w-xl leading-relaxed mb-8">
        Ask questions, upload documents for RAG retrieval, or search the web for the latest information with dynamic LangGraph routing.
      </p>

      {/* 4 Suggestion Feature Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
        {suggestions.map((card, idx) => {
          const Icon = card.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectSuggestion(card.prompt)}
              className="bg-white/80 dark:bg-[#161412]/80 backdrop-blur-md border border-[#e5e7eb] dark:border-[#2b2723] hover:border-[#ff882b] dark:hover:border-[#ff882b] p-5 rounded-2xl text-left flex flex-col justify-between transition-all hover:shadow-lg hover:-translate-y-0.5 group"
            >
              <div className="space-y-3">
                <div
                  className={`w-11 h-11 rounded-xl ${card.iconBg} flex items-center justify-center transition-transform group-hover:scale-110`}
                >
                  <Icon className={`w-5 h-5 ${card.iconColor}`} />
                </div>
                <div>
                  <h2 className="font-semibold text-sm text-[#101010] dark:text-[#f5f5f5] tracking-tight">
                    {card.title}
                  </h2>
                  <p className="text-xs text-[#7a8097] dark:text-[#a1a1aa] mt-1 leading-snug">
                    {card.subtitle}
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-medium text-[#009bff] dark:text-[#ff882b] mt-4 flex items-center space-x-1 group-hover:underline">
                <span>Try prompt</span>
                <span>→</span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
