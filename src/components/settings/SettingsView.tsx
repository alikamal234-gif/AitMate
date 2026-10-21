import React, { useState } from 'react';
import {
  Settings,
  Cpu,
  Globe,
  Lock,
  Trash2,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { HealthResponse } from '../../types/api';

interface SettingsViewProps {
  health: HealthResponse | null;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ health }) => {
  const [clearedMsg, setClearedMsg] = useState<string | null>(null);

  const handleClearLocalSession = () => {
    localStorage.removeItem('aitmate_session_token');
    setClearedMsg('Local session token cleared. Re-bootstrapping from backend...');
    setTimeout(() => {
      window.location.reload();
    }, 1200);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="h-5 w-5 text-emerald-400" />
          Settings & System Safety
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Review active AI provider configuration, approved domain boundaries, and local storage state.
        </p>
      </div>

      {clearedMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          <span>{clearedMsg}</span>
        </div>
      )}

      {/* AI Provider Section */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-purple-400" />
            <h3 className="font-semibold text-white text-sm">AI Provider Management</h3>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Active: {health?.active_provider || 'Mock'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <span className="font-bold text-slate-200">Built-in Safe Mock</span>
            <p className="text-slate-400 text-[11px]">
              Offline deterministic provider without external network transmission or API credits.
            </p>
            <div className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-semibold mt-1">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Offline Ready</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <span className="font-bold text-slate-200">Ollama Local</span>
            <p className="text-slate-400 text-[11px]">
              Local inference at <code className="text-emerald-300">http://127.0.0.1:11434</code>. Private on-premise execution.
            </p>
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mt-1 font-mono">
              llama3.2:latest
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <span className="font-bold text-amber-200">Groq Cloud LPU</span>
            <p className="text-slate-400 text-[11px]">
              Ultra-fast inference via Groq LPUs. Configure <code className="text-amber-300">GROQ_API_KEY</code> in <code className="text-amber-300">.env</code>.
            </p>
            <div className="flex items-center gap-1.5 text-amber-400 text-[11px] font-semibold mt-1">
              <Zap className="h-3.5 w-3.5" />
              <span>llama-3.3-70b-versatile</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security & Domain Allowlist */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-blue-400" />
          <h3 className="font-semibold text-white text-sm">Browser Domain Allowlist</h3>
        </div>
        <p className="text-xs text-slate-400">
          Playwright browser automation is restricted to these approved domains. Any agent attempt to navigate outside this list is immediately blocked by the Central Permission Engine.
        </p>

        <div className="flex flex-wrap gap-2 pt-1">
          {health?.allowed_domains?.map((domain) => (
            <span
              key={domain}
              className="px-3 py-1.5 rounded-lg bg-slate-950 text-xs text-emerald-300 border border-slate-800 font-mono flex items-center gap-1.5"
            >
              <Globe className="h-3.5 w-3.5 text-emerald-400" />
              {domain}
            </span>
          ))}
        </div>
      </div>

      {/* Local Storage & Security Boundaries */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Lock className="h-5 w-5 text-emerald-400" />
          <h3 className="font-semibold text-white text-sm">Local Storage & Boundaries</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-slate-400 text-[11px]">Database Path</span>
            <p className="font-mono text-white font-semibold">./aitmate.db</p>
            <p className="text-slate-500 text-[10px]">SQLite (Encrypted secrets only)</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-slate-400 text-[11px]">Audit Log Stream</span>
            <p className="font-mono text-white font-semibold">./aitmate_audit.log</p>
            <p className="text-slate-500 text-[10px]">JSON-Lines with secret redaction</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-slate-400 text-[11px]">Local Loopback</span>
            <p className="font-mono text-white font-semibold">127.0.0.1:8000</p>
            <p className="text-slate-500 text-[10px]">Strict Bearer token validation</p>
          </div>
        </div>

        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Reset local UI session token and reload credentials from backend:
          </span>
          <button
            onClick={handleClearLocalSession}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-500/15 border border-slate-700 hover:border-rose-500/30 text-xs text-slate-300 hover:text-rose-300 transition flex items-center gap-1.5"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Reset UI Session</span>
          </button>
        </div>
      </div>
    </div>
  );
};
