import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  X,
  Minimize2,
  Maximize2,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../../lib/api-client';
import { TaskRecord } from '../../types/api';

interface FloatingQuickAssistantProps {
  onTaskCreated?: (task: TaskRecord) => void;
  onOpenFullApp?: () => void;
  providerName?: string;
}

export const FloatingQuickAssistant: React.FC<FloatingQuickAssistantProps> = ({
  onTaskCreated,
  onOpenFullApp,
  providerName = 'groq',
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [instruction, setInstruction] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [activeTask, setActiveTask] = useState<TaskRecord | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global Keyboard Shortcut: Alt + A or Ctrl + Space to toggle Hide/Show
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.altKey && e.key.toLowerCase() === 'a') || (e.ctrlKey && e.code === 'Space')) {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      } else if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Focus input automatically when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!instruction.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setStatusMessage('Planning bounded task with ' + providerName + '...');
    setActiveTask(null);

    try {
      const task = await apiClient.createTask(instruction.trim());
      setActiveTask(task);
      setInstruction('');
      if (onTaskCreated) onTaskCreated(task);

      if (task.status === 'completed') {
        setStatusMessage('Task completed successfully!');
      } else if (task.status === 'awaiting_approval') {
        setStatusMessage('Action paused: Human approval required!');
      } else if (task.status === 'failed') {
        setStatusMessage('Task stopped: ' + (task.error || 'Policy denied'));
      } else {
        setStatusMessage('Task status: ' + task.status);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Execution error';
      setStatusMessage('Error: ' + msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button (Always visible in bottom-right corner when collapsed) */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 group">
          <div className="px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-700/80 text-[11px] text-slate-300 shadow-xl backdrop-blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none flex items-center gap-1.5">
            <Sparkles className="h-3 w-3 text-emerald-400" />
            <span>Quick Assistant (Alt + A)</span>
          </div>

          <button
            onClick={() => setIsOpen(true)}
            title="Open Quick Assistant (Alt + A)"
            className="h-14 w-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 hover:from-emerald-500 hover:to-teal-300 text-slate-950 shadow-2xl shadow-emerald-500/30 flex items-center justify-center transition-all duration-300 transform hover:scale-105 active:scale-95 border-2 border-emerald-300/40 cursor-pointer"
          >
            <Bot className="h-7 w-7 text-slate-950 font-bold" />
            <span className="absolute -top-1 -right-1 h-3.5 w-3.5 rounded-full bg-emerald-400 border-2 border-slate-950 animate-ping" />
            <span className="absolute -top-1 -right-1 h-3.5 w-3.5 rounded-full bg-emerald-400 border-2 border-slate-950" />
          </button>
        </div>
      )}

      {/* Floating Expanded Assistant Widget */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-full max-w-lg animate-in fade-in slide-in-from-bottom-5 duration-200 select-none">
          <div className="rounded-3xl bg-slate-900/95 border border-slate-700/80 shadow-2xl shadow-black/80 backdrop-blur-2xl overflow-hidden flex flex-col">
            {/* Widget Top Header */}
            <div className="p-3.5 px-4 bg-slate-950/70 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="h-7 w-7 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
                    AitMate Quick Assistant
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                      {providerName}
                    </span>
                  </h3>
                  <p className="text-[10px] text-slate-400">Press Esc or click hide to minimize</p>
                </div>
              </div>

              <div className="flex items-center gap-1">
                {onOpenFullApp && (
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      onOpenFullApp();
                    }}
                    title="Open Full Dashboard"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                  >
                    <Maximize2 className="h-3.5 w-3.5" />
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  title="Hide Assistant (Esc)"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  <Minimize2 className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  title="Close (Esc)"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Input Bar */}
            <form onSubmit={handleSubmit} className="p-3 bg-slate-950/30">
              <div className="relative flex items-center">
                <input
                  ref={inputRef}
                  type="text"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  disabled={isSubmitting}
                  placeholder="Tell AitMate what to do... (e.g. 'Read README.md', 'Check Git status')"
                  className="w-full pl-3.5 pr-11 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700/80 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/50 transition"
                />
                <button
                  type="submit"
                  disabled={isSubmitting || !instruction.trim()}
                  className="absolute right-1.5 p-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-slate-950 transition font-bold"
                >
                  {isSubmitting ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Send className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>
            </form>

            {/* Status Feedback Pill */}
            {statusMessage && (
              <div className="px-4 py-2 bg-slate-950/50 border-t border-slate-800/80 text-[11px] flex items-center justify-between">
                <div className="flex items-center gap-2 truncate">
                  {isSubmitting ? (
                    <Loader2 className="h-3.5 w-3.5 text-emerald-400 animate-spin shrink-0" />
                  ) : activeTask?.status === 'completed' ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                  ) : activeTask?.status === 'awaiting_approval' ? (
                    <ShieldAlert className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                  ) : (
                    <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                  )}
                  <span className="text-slate-300 font-medium truncate">{statusMessage}</span>
                </div>

                {activeTask?.status === 'awaiting_approval' && onOpenFullApp && (
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      onOpenFullApp();
                    }}
                    className="ml-2 px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 text-[10px] font-bold shrink-0"
                  >
                    Review Now
                  </button>
                )}
              </div>
            )}

            {/* Steps Preview if active task */}
            {activeTask && activeTask.plan && activeTask.plan.length > 0 && (
              <div className="p-3 bg-slate-950/60 border-t border-slate-800 max-h-36 overflow-y-auto space-y-1.5 text-[11px]">
                {activeTask.plan.map((step, idx) => (
                  <div
                    key={idx}
                    className="p-1.5 px-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between"
                  >
                    <span className="text-slate-300 truncate">
                      {step.step_number}. {step.description}
                    </span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                        step.status === 'completed'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : step.status === 'failed'
                          ? 'bg-rose-500/20 text-rose-300'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {step.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
