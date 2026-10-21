import { useState, useEffect } from 'react';
import {
  Bot,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Activity,
  ListTodo,
  Settings,
  MessageSquare,
  RefreshCw,
  Globe,
  Database,
  Lock,
  Cpu
} from 'lucide-react';
import { apiClient } from './lib/api-client';
import { HealthResponse, SystemStatusResponse } from './types/api';

type NavTab = 'chat' | 'tasks' | 'approvals' | 'activity' | 'settings';

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('chat');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Check health and bootstrap local session
  const checkConnection = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const healthData = await apiClient.getHealth();
      setHealth(healthData);

      // Bootstrap session token from loopback
      await apiClient.bootstrapSession();

      // Retrieve authenticated system status
      const statusData = await apiClient.getSystemStatus();
      setSystemStatus(statusData);

      setBackendConnected(true);
    } catch (err: unknown) {
      setBackendConnected(false);
      const message = err instanceof Error ? err.message : 'Failed to reach local backend';
      setErrorMsg(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 bg-grid-pattern">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-800/80 bg-slate-900/60 backdrop-blur-xl flex flex-col shrink-0 select-none">
        {/* App Brand */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Bot className="h-5 w-5 text-slate-950 font-bold" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                AitMate
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  v0.1
                </span>
              </h1>
              <p className="text-[11px] text-slate-400 font-medium">Desktop AI Agent</p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
          <button
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'chat'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            <span>Command Center</span>
          </button>

          <button
            onClick={() => setActiveTab('tasks')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'tasks'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <div className="flex items-center space-x-3">
              <ListTodo className="h-4 w-4" />
              <span>Tasks</span>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
              {systemStatus?.active_tasks || 0}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('approvals')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'approvals'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <div className="flex items-center space-x-3">
              <ShieldCheck className="h-4 w-4" />
              <span>Approval Center</span>
            </div>
            {systemStatus && systemStatus.pending_approvals > 0 ? (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">
                {systemStatus.pending_approvals}
              </span>
            ) : (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                0
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('activity')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'activity'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>Activity Audit</span>
          </button>

          <button
            onClick={() => setActiveTab('settings')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'settings'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Settings className="h-4 w-4" />
            <span>Settings & Safety</span>
          </button>
        </nav>

        {/* Security & Backend Indicator */}
        <div className="p-3.5 border-t border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-emerald-400" />
              Local Loopback
            </span>
            <span className="font-mono text-[11px] text-slate-300">127.0.0.1:8000</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  backendConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
                }`}
              />
              <span className="text-[11px] font-medium text-slate-300">
                {backendConnected ? 'Backend Online' : 'Connecting...'}
              </span>
            </div>
            <button
              onClick={checkConnection}
              disabled={isLoading}
              title="Ping Backend"
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-14 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md px-6 flex items-center justify-between select-none shrink-0">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              {activeTab === 'chat' && 'Command Center'}
              {activeTab === 'tasks' && 'Active & Queued Tasks'}
              {activeTab === 'approvals' && 'Human Approval Gates'}
              {activeTab === 'activity' && 'Security Audit Log'}
              {activeTab === 'settings' && 'System Configuration'}
            </span>
          </div>

          <div className="flex items-center space-x-3">
            {/* AI Provider Tag */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs">
              <Cpu className="h-3.5 w-3.5 text-purple-400" />
              <span className="text-slate-300 font-medium">Provider:</span>
              <span className="font-mono text-emerald-400">
                {health?.active_provider || 'Local Mock'}
              </span>
            </div>

            {/* Safety Guard Indicator */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span className="font-medium">Permission Engine Active</span>
            </div>
          </div>
        </header>

        {/* Viewport Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Connection Error Banner if Backend is down */}
          {!backendConnected && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-xs">
                <h2 className="font-semibold text-rose-300">Local Backend Offline</h2>
                <p className="text-slate-300 mt-1">
                  AitMate requires the local Python agent service running on{' '}
                  <code className="text-rose-200">127.0.0.1:8000</code>.
                </p>
                <p className="text-slate-400 mt-1 font-mono text-[11px]">
                  Start command: python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
                </p>
                {errorMsg && <p className="text-rose-400/80 mt-1">Details: {errorMsg}</p>}
              </div>
            </div>
          )}

          {/* Tab 1: Command Center / Chat */}
          {activeTab === 'chat' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-900/80 to-slate-900/40 border border-slate-800 shadow-xl space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-white tracking-tight">
                      Welcome to AitMate
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Useful autonomy, with the user in control. Submit instructions, inspect
                      execution plans, and approve sensitive actions.
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
                    <Globe className="h-3.5 w-3.5 text-blue-400" />
                    <span>Allowed domains: {health?.allowed_domains?.length || 4}</span>
                  </div>
                </div>

                {/* Instruction Input Box */}
                <div className="mt-4 p-3 rounded-xl bg-slate-950/80 border border-slate-800 focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/30 transition">
                  <textarea
                    rows={3}
                    placeholder="E.g., Summarize latest tech news from wikipedia.org and draft a briefing..."
                    className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none"
                  />
                  <div className="mt-2 pt-2 border-t border-slate-900 flex items-center justify-between text-xs text-slate-400">
                    <span className="flex items-center gap-1.5 text-[11px]">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                      Actions verified by server policy before execution
                    </span>
                    <button className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-semibold text-xs transition shadow-md shadow-emerald-600/20">
                      Submit Task
                    </button>
                  </div>
                </div>
              </div>

              {/* System Architecture Readiness Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-medium">FastAPI Backend</span>
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  </div>
                  <p className="text-sm font-semibold text-white">
                    {backendConnected ? 'Operational (127.0.0.1)' : 'Offline'}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Version: {health?.version || '0.1.0'} | Port: 8000
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-medium">Security Boundary</span>
                    <Lock className="h-4 w-4 text-emerald-400" />
                  </div>
                  <p className="text-sm font-semibold text-white">Bearer Auth Active</p>
                  <p className="text-[11px] text-slate-400 font-mono">
                    Token: {systemStatus?.session_token_prefix || 'Active'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-medium">Local SQLite Store</span>
                    <Database className="h-4 w-4 text-emerald-400" />
                  </div>
                  <p className="text-sm font-semibold text-white">aitmate.db</p>
                  <p className="text-[11px] text-slate-400">Append-only audit & tasks</p>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Tasks */}
          {activeTab === 'tasks' && (
            <div className="max-w-4xl mx-auto space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-white">Task Lifecycle Monitor</h2>
                <span className="text-xs text-slate-400">
                  Total Active: {systemStatus?.active_tasks || 0}
                </span>
              </div>
              <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-2">
                <ListTodo className="h-8 w-8 text-slate-600 mx-auto" />
                <h3 className="text-sm font-medium text-slate-300">No active tasks running</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  Submit a prompt in the Command Center to initiate a multi-step bounded agent task.
                </p>
              </div>
            </div>
          )}

          {/* Tab 3: Approvals */}
          {activeTab === 'approvals' && (
            <div className="max-w-4xl mx-auto space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white">Approval Center</h2>
                  <p className="text-xs text-slate-400">
                    High-risk operations are blocked server-side until you review and authorize them.
                  </p>
                </div>
              </div>
              <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center space-y-2">
                <ShieldCheck className="h-8 w-8 text-emerald-500/60 mx-auto" />
                <h3 className="text-sm font-medium text-slate-300">All clear — No pending approvals</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  When a task attempts a sensitive action (message sending, external form submission,
                  or file modifications), an approval request with the exact payload will appear here.
                </p>
              </div>
            </div>
          )}

          {/* Tab 4: Activity */}
          {activeTab === 'activity' && (
            <div className="max-w-4xl mx-auto space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-white">Auditable Event Log</h2>
                <span className="text-xs text-slate-400 font-mono">aitmate_audit.log</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-xs text-slate-400 space-y-2">
                <div className="flex items-center justify-between text-slate-500 text-[11px] border-b border-slate-800/80 pb-1">
                  <span>TIMESTAMP</span>
                  <span>EVENT</span>
                  <span>TARGET</span>
                </div>
                <div className="flex items-center justify-between text-slate-300 py-1">
                  <span>{new Date().toLocaleTimeString()}</span>
                  <span className="text-emerald-400 font-semibold">SYSTEM_BOOTSTRAP</span>
                  <span>127.0.0.1:8000</span>
                </div>
                <div className="flex items-center justify-between text-slate-300 py-1">
                  <span>{new Date().toLocaleTimeString()}</span>
                  <span className="text-blue-400 font-semibold">HEALTH_VERIFIED</span>
                  <span>/api/v1/health</span>
                </div>
              </div>
            </div>
          )}

          {/* Tab 5: Settings */}
          {activeTab === 'settings' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
                <h2 className="text-base font-bold text-white">AI Provider Configuration</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <span className="font-semibold text-slate-200">Active Provider</span>
                    <p className="text-emerald-400 font-mono font-medium">
                      {health?.active_provider || 'Mock (Safe Offline)'}
                    </p>
                    <p className="text-slate-400 text-[11px]">
                      Runs offline deterministically without consuming API credits or sending data off-device.
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <span className="font-semibold text-slate-200">Ollama Local Integration</span>
                    <p className="text-slate-400 font-mono text-[11px]">http://127.0.0.1:11434</p>
                    <p className="text-slate-400 text-[11px]">
                      Configurable in <code className="text-emerald-300">.env</code> for private on-device LLMs.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
                <h2 className="text-base font-bold text-white">Browser Domain Allowlist</h2>
                <div className="flex flex-wrap gap-2">
                  {health?.allowed_domains?.map((domain) => (
                    <span
                      key={domain}
                      className="px-2.5 py-1 rounded-md bg-slate-800 text-xs text-slate-300 border border-slate-700/60 font-mono flex items-center gap-1"
                    >
                      <Globe className="h-3 w-3 text-emerald-400" />
                      {domain}
                    </span>
                  )) || <span className="text-xs text-slate-500">None configured</span>}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
