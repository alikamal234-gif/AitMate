import React, { useState } from 'react';
import {
  Send,
  ShieldCheck,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  Sparkles,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { apiClient } from '../../lib/api-client';
import { PlanStep, TaskRecord } from '../../types/api';

interface CommandCenterProps {
  onTaskCreated: (task: TaskRecord) => void;
  onNavigateToApprovals: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  onTaskCreated,
  onNavigateToApprovals,
}) => {
  const [instruction, setInstruction] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentTask, setCurrentTask] = useState<TaskRecord | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const samplePrompts = [
    'Check application status and summarize system readiness',
    'Summarize AitMate architecture rules and security policies',
    'Draft a release announcement for AitMate desktop assistant',
    'Transmit security audit alert to external channel (Approval Required)',
  ];

  const handleSubmit = async (promptToUse?: string) => {
    const prompt = (promptToUse || instruction).trim();
    if (!prompt || isSubmitting) return;

    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const task = await apiClient.createTask(prompt);
      setCurrentTask(task);
      onTaskCreated(task);
      setInstruction('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to launch task';
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (!currentTask) return;
    try {
      await apiClient.cancelTask(currentTask.id);
      const updated = await apiClient.getTask(currentTask.id);
      setCurrentTask(updated);
    } catch (err: unknown) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-900/50 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-emerald-400" />
              Command Center
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Natural-language task executor. Every step is bounded, audited, and policy-checked before execution.
            </p>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4" />
            <span>Human Approval Gates Active</span>
          </div>
        </div>

        {/* Input Textarea Box */}
        <div className="mt-4 p-3 rounded-xl bg-slate-950/90 border border-slate-800 focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/30 transition">
          <textarea
            rows={3}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Type an instruction (e.g., 'Check system status and summarize readiness')..."
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none"
          />
          <div className="mt-2 pt-2 border-t border-slate-900 flex items-center justify-between text-xs text-slate-400">
            <span className="text-[11px] text-slate-500">
              Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">Enter</kbd> to submit
            </span>
            <button
              onClick={() => handleSubmit()}
              disabled={isSubmitting || !instruction.trim()}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-slate-950 font-semibold text-xs transition flex items-center gap-1.5 shadow-md shadow-emerald-600/20"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Planning...</span>
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  <span>Execute Task</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="space-y-2">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Quick Scenarios
          </span>
          <div className="flex flex-wrap gap-2">
            {samplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSubmit(prompt)}
                className="text-left px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-600 text-xs text-slate-300 transition flex items-center gap-1.5 group"
              >
                <span>{prompt}</span>
                <ArrowRight className="h-3 w-3 text-slate-500 group-hover:text-emerald-400 transition" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Active / Most Recent Task Monitor */}
      {currentTask && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-mono">Task ID: {currentTask.id.slice(0, 8)}...</span>
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full font-semibold border ${
                    currentTask.status === 'completed'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : currentTask.status === 'awaiting_approval'
                      ? 'bg-amber-500/15 text-amber-300 border-amber-500/30 animate-pulse'
                      : currentTask.status === 'failed'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      : currentTask.status === 'cancelled'
                      ? 'bg-slate-800 text-slate-400 border-slate-700'
                      : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                  }`}
                >
                  {currentTask.status.toUpperCase()}
                </span>
              </div>
              <h3 className="font-semibold text-white text-sm mt-1">{currentTask.instruction}</h3>
            </div>

            {/* Cancel Button if active */}
            {['queued', 'planning', 'running', 'awaiting_approval'].includes(currentTask.status) && (
              <button
                onClick={handleCancel}
                className="px-3 py-1 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-xs font-medium transition"
              >
                Cancel Task
              </button>
            )}
          </div>

          {/* If Task is Paused at Approval Gate */}
          {currentTask.status === 'awaiting_approval' && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start justify-between">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-amber-300">Action Awaiting Your Approval</h4>
                  <p className="text-xs text-slate-300 mt-0.5">
                    A sensitive tool call has been paused by the Central Permission Engine.
                  </p>
                </div>
              </div>
              <button
                onClick={onNavigateToApprovals}
                className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition"
              >
                Review in Approval Center
              </button>
            </div>
          )}

          {/* Bounded Execution Plan Steps */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Bounded Execution Plan ({currentTask.plan?.length || 0} Steps)
            </span>
            <div className="space-y-2">
              {currentTask.plan?.map((step: PlanStep, index: number) => (
                <div
                  key={index}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center space-x-3">
                    <span className="h-5 w-5 rounded-full bg-slate-800 flex items-center justify-center font-mono text-[10px] text-slate-300">
                      {step.step_number}
                    </span>
                    <div>
                      <span className="font-semibold text-slate-200">{step.description}</span>
                      <p className="text-[11px] font-mono text-slate-500">
                        Tool: <span className="text-emerald-400">{step.tool_name}</span> | Target: {step.target}
                      </p>
                    </div>
                  </div>

                  {/* Step Status Badge */}
                  <div>
                    {step.status === 'completed' && (
                      <span className="flex items-center gap-1 text-emerald-400 text-[11px] font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Completed
                      </span>
                    )}
                    {step.status === 'running' && (
                      <span className="flex items-center gap-1 text-blue-400 text-[11px] font-medium">
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Running
                      </span>
                    )}
                    {step.status === 'pending' && (
                      <span className="flex items-center gap-1 text-slate-500 text-[11px]">
                        <Clock className="h-3.5 w-3.5" /> Pending
                      </span>
                    )}
                    {step.status === 'failed' && (
                      <span className="flex items-center gap-1 text-rose-400 text-[11px] font-medium">
                        <XCircle className="h-3.5 w-3.5" /> Failed
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Final Summary or Error Result */}
          {currentTask.summary && (
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 space-y-1">
              <span className="font-bold flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Outcome Summary
              </span>
              <p className="text-slate-200">{currentTask.summary}</p>
            </div>
          )}
          {currentTask.error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 space-y-1">
              <span className="font-bold flex items-center gap-1">
                <AlertCircle className="h-3.5 w-3.5 text-rose-400" /> Error Details
              </span>
              <p className="text-slate-200">{currentTask.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
