import React, { useState, useEffect } from 'react';
import {
  ListTodo,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Ban
} from 'lucide-react';
import { apiClient } from '../../lib/api-client';
import { PlanStep, TaskRecord } from '../../types/api';

export const TasksView: React.FC = () => {
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchTasks = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getTasks(30);
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCancel = async (taskId: string) => {
    try {
      await apiClient.cancelTask(taskId);
      await fetchTasks();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <ListTodo className="h-5 w-5 text-emerald-400" />
            Task Lifecycle Monitor
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time execution telemetry and state history. All transitions are deterministic and audited.
          </p>
        </div>
        <button
          onClick={fetchTasks}
          disabled={isLoading}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition flex items-center gap-1.5 text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
          <ListTodo className="h-10 w-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">No tasks created yet</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Submit an instruction in the Command Center to initiate multi-step agent workflows.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task: TaskRecord) => {
            const isExpanded = expandedTaskId === task.id;
            return (
              <div
                key={task.id}
                className="rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition overflow-hidden shadow-sm"
              >
                <div
                  className="p-4 flex items-center justify-between cursor-pointer select-none"
                  onClick={() => setExpandedTaskId(isExpanded ? null : task.id)}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] text-slate-500">
                        {task.id.slice(0, 8)}...
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                          task.status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : task.status === 'awaiting_approval'
                            ? 'bg-amber-500/15 text-amber-300 border-amber-500/30 animate-pulse'
                            : task.status === 'failed'
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                            : task.status === 'cancelled'
                            ? 'bg-slate-800 text-slate-400 border-slate-700'
                            : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                        }`}
                      >
                        {task.status.toUpperCase()}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        {new Date(task.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <h3 className="font-semibold text-slate-200 text-sm">{task.instruction}</h3>
                  </div>

                  <div className="flex items-center gap-3">
                    {['queued', 'planning', 'running', 'awaiting_approval'].includes(task.status) && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCancel(task.id);
                        }}
                        className="px-2.5 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-xs flex items-center gap-1 transition"
                      >
                        <Ban className="h-3 w-3" />
                        <span>Cancel</span>
                      </button>
                    )}
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details & Plan */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 border-t border-slate-800/80 bg-slate-950/40 space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>
                        Plan Steps: {task.current_step_index} / {task.plan?.length || 0} executed
                      </span>
                      {task.completed_at && (
                        <span>
                          Completed at: {new Date(task.completed_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>

                    <div className="space-y-2">
                      {task.plan?.map((step: PlanStep, idx: number) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-300">
                              Step {step.step_number}: {step.description}
                            </span>
                            <span className="text-[10px] font-mono text-emerald-400">
                              {step.tool_name}
                            </span>
                          </div>
                          {step.result && (
                            <p className="font-mono text-[11px] text-slate-400 truncate">
                              Result: {step.result}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>

                    {task.summary && (
                      <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
                        <span className="font-bold">Summary: </span>
                        {task.summary}
                      </div>
                    )}
                    {task.error && (
                      <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
                        <span className="font-bold">Error: </span>
                        {task.error}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
