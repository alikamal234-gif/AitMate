import React, { useState, useEffect } from 'react';
import {
  Activity,
  RefreshCw
} from 'lucide-react';
import { apiClient } from '../../lib/api-client';
import { AuditEvent } from '../../types/api';

export const ActivityView: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [filterType, setFilterType] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);

  const fetchActivity = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getActivity(50);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load activity log:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActivity();
    const interval = setInterval(fetchActivity, 6000);
    return () => clearInterval(interval);
  }, []);

  const filteredEvents =
    filterType === 'all'
      ? events
      : events.filter((e) => e.event_type.toLowerCase().includes(filterType.toLowerCase()));

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-400" />
            Security & Operational Audit Log
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident, append-only log of every state transition, tool invocation, and human approval. Secrets are automatically redacted.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Filter Dropdown */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300 px-3 py-1.5 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Events</option>
            <option value="task_created">Task Created</option>
            <option value="tool_invoked">Tool Invoked</option>
            <option value="approval">Approvals</option>
            <option value="security">Security Alerts</option>
          </select>

          <button
            onClick={fetchActivity}
            disabled={isLoading}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {filteredEvents.length === 0 ? (
        <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
          <Activity className="h-10 w-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">No matching audit events</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Audit logs will be generated automatically as tasks are planned, approved, and executed.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {filteredEvents.map((event) => {
            const isSecurity =
              event.event_type.includes('security') || event.event_type.includes('violation');
            const isApproval = event.event_type.includes('approval');
            const isCompleted = event.event_type.includes('completed');

            return (
              <div
                key={event.id}
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start justify-between text-xs transition hover:border-slate-700/80"
              >
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                        isSecurity
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : isApproval
                          ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                          : isCompleted
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {event.event_type}
                    </span>
                    {event.tool_name && (
                      <span className="font-mono text-[11px] text-emerald-400">
                        tool: {event.tool_name}
                      </span>
                    )}
                    {event.task_id && (
                      <span className="font-mono text-[10px] text-slate-500">
                        task: {event.task_id.slice(0, 8)}...
                      </span>
                    )}
                  </div>
                  <p className="text-slate-200 font-medium text-xs">{event.summary}</p>
                </div>

                <div className="text-right text-[11px] font-mono text-slate-500 shrink-0">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
