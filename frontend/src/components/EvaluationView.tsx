import React, { useState } from 'react';
import {
  Play,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { runEvaluationSuite } from '../services/api';
import type { EvalResponse } from '../types';

interface EvaluationViewProps {
  onBack: () => void;
}

export const EvaluationView: React.FC<EvaluationViewProps> = ({ onBack }) => {
  const [numQuestions, setNumQuestions] = useState(5);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [results, setResults] = useState<EvalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunEval = async () => {
    try {
      setIsEvaluating(true);
      setError(null);
      setResults(null);
      const res = await runEvaluationSuite({
        num_questions: numQuestions,
      });
      setResults(res);
    } catch (e: any) {
      setError(e.message || 'Evaluation failed.');
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6 overflow-y-auto select-none">
      <div className="flex items-center space-x-3 mb-2">
        <button
          onClick={onBack}
          className="p-2 rounded-xl text-[#94a3b8] hover:bg-[#f1f5f9] dark:hover:bg-[#201d1a] transition-colors"
        >
          ← Back to Chat
        </button>
        <h1 className="text-xl font-bold text-[#0f172a] dark:text-[#f8fafc]">
          Benchmark Evaluation Suite
        </h1>
      </div>

      {/* Upload & Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-3xl bg-white dark:bg-[#141210] border border-[#e2e8f0] dark:border-[#2b2723]">
          <label className="block text-sm font-semibold mb-3 text-[#0f172a] dark:text-[#f8fafc]">
            Benchmark Configuration
          </label>
          <div className="space-y-4">
            <p className="text-xs text-[#64748b] dark:text-[#a1a1aa]">
              Tests routing accuracy, answer latency, and retrieval fidelity against the verified benchmark questions dataset.
            </p>
            <div>
              <label className="text-xs text-[#64748b] dark:text-[#a1a1aa] block mb-2 font-medium">
                Number of Questions to Evaluate: {numQuestions}
              </label>
              <input
                type="range"
                min="1"
                max="25"
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="w-full h-1.5 bg-[#e2e8f0] dark:bg-[#2b2723] rounded-lg appearance-none cursor-pointer accent-[#ff882b]"
              />
            </div>
          </div>
        </div>

        <div className="p-6 rounded-3xl bg-white dark:bg-[#141210] border border-[#e2e8f0] dark:border-[#2b2723] flex flex-col justify-center items-center text-center">
          <button
            onClick={handleRunEval}
            disabled={isEvaluating}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#009bff] to-[#ff882b] text-white font-semibold shadow-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
          >
            {isEvaluating ? (
              <RotateCcw className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            <span>{isEvaluating ? 'Running Benchmark...' : 'Start Benchmark Evaluation'}</span>
          </button>
          {error && <p className="mt-4 text-rose-500 text-xs">{error}</p>}
        </div>
      </div>

      {/* Results View */}
      {results && (
        <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              label="Mode Accuracy"
              value={`${results.summary.mode_accuracy_pct.toFixed(1)}%`}
              color="text-emerald-500"
            />
            <MetricCard
              label="Avg Latency"
              value={`${results.summary.avg_latency_seconds.toFixed(2)}s`}
              color="text-[#009bff]"
            />
            <MetricCard
              label="Total Executed"
              value={`${results.summary.successful_runs}/${results.summary.total_questions}`}
              color="text-[#ff882b]"
            />
          </div>

          <div className="p-6 rounded-3xl bg-white dark:bg-[#141210] border border-[#e2e8f0] dark:border-[#2b2723]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm text-[#0f172a] dark:text-[#f8fafc]">
                Evaluation Run Details
              </h3>
              <span className="text-xs text-[#64748b]">Model: {results.summary.model_used}</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="border-b border-[#e2e8f0] dark:border-[#2b2723] text-[#64748b]">
                  <tr>
                    <th className="p-3">#</th>
                    <th className="p-3">Question</th>
                    <th className="p-3">Expected Mode</th>
                    <th className="p-3">Actual Mode</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">Verdict</th>
                  </tr>
                </thead>
                <tbody>
                  {results.results.map((row) => (
                    <tr
                      key={row.question_id}
                      className="border-b border-[#f1f5f9] dark:border-[#201d1a]"
                    >
                      <td className="p-3 font-mono">{row.question_id}</td>
                      <td className="p-3 truncate max-w-xs">{row.question}</td>
                      <td className="p-3 font-mono text-[11px]">{row.expected_mode || 'N/A'}</td>
                      <td className="p-3 font-mono text-[11px]">{row.actual_mode}</td>
                      <td className="p-3">{row.latency_seconds.toFixed(2)}s</td>
                      <td className="p-3">
                        {row.mode_correct ? (
                          <div className="flex items-center space-x-1 text-emerald-500">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>Passed</span>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-1 text-rose-500">
                            <AlertTriangle className="w-4 h-4" />
                            <span>Mismatch</span>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const MetricCard: React.FC<{ label: string; value: string; color: string }> = ({
  label,
  value,
  color,
}) => (
  <div className="p-6 rounded-3xl bg-white dark:bg-[#141210] border border-[#e2e8f0] dark:border-[#2b2723]">
    <p className="text-xs text-[#64748b] mb-1">{label}</p>
    <p className={`text-2xl font-bold ${color}`}>{value}</p>
  </div>
);
