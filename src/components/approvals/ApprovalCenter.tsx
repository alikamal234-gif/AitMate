import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  FileCode
} from 'lucide-react';
import { apiClient } from '../../lib/api-client';
import { ApprovalRecord } from '../../types/api';

interface ApprovalCenterProps {
  onApprovalResolved?: () => void;
}

export const ApprovalCenter: React.FC<ApprovalCenterProps> = ({ onApprovalResolved }) => {
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [filter, setFilter] = useState<'pending' | 'resolved'>('pending');
  const [isLoading, setIsLoading] = useState(false);
  const [decidingId, setDecidingId] = useState<string | null>(null);

  const fetchApprovals = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getApprovals(filter === 'pending' ? 'pending' : '');
      const filtered =
        filter === 'pending'
          ? data.filter((a) => a.status === 'pending')
          : data.filter((a) => a.status !== 'pending');
      setApprovals(filtered);
    } catch (err) {
      console.error('Failed to load approvals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
    const interval = setInterval(fetchApprovals, 4000);
    return () => clearInterval(interval);
  }, [filter]);

  const handleDecision = async (approvalId: string, decision: 'approve' | 'reject') => {
    setDecidingId(approvalId);
    try {
      await apiClient.decideApproval(approvalId, decision);
      await fetchApprovals();
      if (onApprovalResolved) onApprovalResolved();
    } catch (err) {
      console.error('Decision failed:', err);
    } finally {
      setDecidingId(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            Human Approval Center
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Zero silent side-effects. Sensitive or consequential actions are blocked server-side until explicitly authorized.
          </p>
        </div>

        {/* Filter Toggle */}
        <div className="flex items-center space-x-1 p-1 bg-slate-900 border border-slate-800 rounded-lg text-xs">
          <button
            onClick={() => setFilter('pending')}
            className={`px-3 py-1 rounded-md transition ${
              filter === 'pending'
                ? 'bg-emerald-500/15 text-emerald-300 font-semibold border border-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Pending ({filter === 'pending' ? approvals.length : '...'})
          </button>
          <button
            onClick={() => setFilter('resolved')}
            className={`px-3 py-1 rounded-md transition ${
              filter === 'resolved'
                ? 'bg-emerald-500/15 text-emerald-300 font-semibold border border-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Resolved History
          </button>
          <button
            onClick={fetchApprovals}
            disabled={isLoading}
            className="p-1 rounded text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {approvals.length === 0 ? (
        <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
          <ShieldCheck className="h-10 w-10 text-emerald-500/50 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">
            {filter === 'pending' ? 'All clear — Zero pending approvals' : 'No resolved approval history'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {filter === 'pending'
              ? 'When an agent task proposes an external transmission, message sending, or mutation, review cards will appear here.'
              : 'Past human authorization decisions are permanently recorded in the audit log.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((approval) => {
            const isPending = approval.status === 'pending';
            const isProcessing = decidingId === approval.id;

            return (
              <div
                key={approval.id}
                className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-md space-y-4"
              >
                {/* Card Header */}
                <div className="flex items-start justify-between border-b border-slate-800/80 pb-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold">
                        {approval.risk_level} RISK
                      </span>
                      <span className="font-mono text-[11px] text-slate-400">
                        Tool: <strong className="text-white">{approval.tool_name}</strong>
                      </span>
                      <span className="text-[11px] text-slate-500">
                        Task: {approval.task_id.slice(0, 8)}...
                      </span>
                    </div>
                    <h3 className="text-sm font-semibold text-white mt-1">
                      Target: <span className="text-emerald-400 font-mono">{approval.target}</span>
                    </h3>
                  </div>

                  {/* Status Badge */}
                  <div>
                    {approval.status === 'approved' && (
                      <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Approved
                      </span>
                    )}
                    {approval.status === 'rejected' && (
                      <span className="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-semibold flex items-center gap-1">
                        <XCircle className="h-3.5 w-3.5" /> Rejected
                      </span>
                    )}
                    {approval.status === 'expired' && (
                      <span className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 text-xs font-semibold flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" /> Expired
                      </span>
                    )}
                  </div>
                </div>

                {/* Reason & Justification */}
                <div className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 space-y-1">
                  <span className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider">
                    Agent Justification
                  </span>
                  <p>{approval.reason}</p>
                </div>

                {/* Exact Parameters Payload Diff */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="font-semibold flex items-center gap-1">
                      <FileCode className="h-3.5 w-3.5 text-emerald-400" /> Exact Parameters (Cryptographically Verified)
                    </span>
                    <span className="text-slate-500 font-mono text-[10px]">
                      Expires: {new Date(approval.expires_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <pre className="p-3 rounded-xl bg-slate-950 border border-slate-900 font-mono text-[11px] text-emerald-300 overflow-x-auto max-h-36">
                    {JSON.stringify(approval.parameters, null, 2)}
                  </pre>
                </div>

                {/* Action Buttons for Pending Approval */}
                {isPending && (
                  <div className="pt-2 flex items-center justify-end space-x-3">
                    <button
                      onClick={() => handleDecision(approval.id, 'reject')}
                      disabled={isProcessing}
                      className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-rose-500/20 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-500/30 text-xs font-semibold transition flex items-center gap-1.5"
                    >
                      <XCircle className="h-4 w-4" />
                      <span>Deny Action</span>
                    </button>
                    <button
                      onClick={() => handleDecision(approval.id, 'approve')}
                      disabled={isProcessing}
                      className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 text-xs font-bold transition shadow-lg shadow-emerald-600/20 flex items-center gap-1.5"
                    >
                      {isProcessing ? (
                        <>
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-4 w-4" />
                          <span>Authorize & Execute</span>
                        </>
                      )}
                    </button>
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
