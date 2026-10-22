import { useState, useEffect } from 'react';
import {
  Bot,
  ShieldCheck,
  Activity,
  ListTodo,
  Settings,
  MessageSquare,
  RefreshCw,
  Lock,
  Cpu,
  AlertTriangle
} from 'lucide-react';
import { apiClient } from './lib/api-client';
import { HealthResponse, SystemStatusResponse, TaskRecord } from './types/api';
import { CommandCenter } from './components/chat/CommandCenter';
import { TasksView } from './components/tasks/TasksView';
import { ApprovalCenter } from './components/approvals/ApprovalCenter';
import { ActivityView } from './components/activity/ActivityView';
import { SettingsView } from './components/settings/SettingsView';
import { FloatingQuickAssistant } from './components/widget/FloatingQuickAssistant';

type NavTab = 'chat' | 'tasks' | 'approvals' | 'activity' | 'settings';

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('chat');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [pendingApprovalCount, setPendingApprovalCount] = useState<number>(0);
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

      // Fetch pending approvals count
      const approvals = await apiClient.getApprovals('pending');
      setPendingApprovalCount(approvals.length);

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
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleTaskCreated = (_task: TaskRecord) => {
    checkConnection();
  };

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
            {pendingApprovalCount > 0 ? (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse font-bold">
                {pendingApprovalCount}
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
        <div className="flex-1 overflow-y-auto p-6">
          {/* Connection Error Banner if Backend is down */}
          {!backendConnected && (
            <div className="max-w-4xl mx-auto mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-xs">
                <h2 className="font-semibold text-rose-300">Local Backend Offline</h2>
                <p className="text-slate-300 mt-1">
                  AitMate requires the local Python agent service running on{' '}
                  <code className="text-rose-200">127.0.0.1:8000</code>.
                </p>
                {errorMsg && <p className="text-rose-400/80 mt-1">Details: {errorMsg}</p>}
              </div>
            </div>
          )}

          {/* Tab 1: Command Center */}
          {activeTab === 'chat' && (
            <CommandCenter
              onTaskCreated={handleTaskCreated}
              onNavigateToApprovals={() => setActiveTab('approvals')}
            />
          )}

          {/* Tab 2: Tasks View */}
          {activeTab === 'tasks' && <TasksView />}

          {/* Tab 3: Approvals View */}
          {activeTab === 'approvals' && (
            <ApprovalCenter onApprovalResolved={checkConnection} />
          )}

          {/* Tab 4: Activity View */}
          {activeTab === 'activity' && <ActivityView />}

          {/* Tab 5: Settings View */}
          {activeTab === 'settings' && (
            <SettingsView health={health} />
          )}
        </div>
      </main>

      {/* Floating Quick Assistant (Hideable / Showable Floating Pill with Alt + A) */}
      <FloatingQuickAssistant
        onTaskCreated={handleTaskCreated}
        onOpenFullApp={() => setActiveTab('chat')}
        providerName={health?.active_provider || 'groq'}
      />
    </div>
  );
}
