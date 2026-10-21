/**
 * Typed API Contracts for AitMate Desktop UI & Backend Communication.
 */

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  bound_host: string;
  bound_port: number;
  active_provider: string;
  allowed_domains: string[];
  timestamp: string;
}

export interface SessionBootstrapResponse {
  app_name: string;
  version: string;
  token: string;
  provider: string;
  allowed_domains: string[];
}

export interface SystemStatusResponse {
  status: string;
  version: string;
  active_tasks: number;
  pending_approvals: number;
  db_connected: boolean;
  provider_available: boolean;
  allowed_domains_count: number;
  session_token_prefix: string;
}

export type TaskStatus =
  | 'queued'
  | 'planning'
  | 'awaiting_approval'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface PlanStep {
  step_number: number;
  description: string;
  tool_name: string;
  target?: string;
  requires_approval: boolean;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'rejected' | 'skipped';
  result?: string;
}

export interface TaskRecord {
  id: string;
  instruction: string;
  status: TaskStatus;
  plan: PlanStep[];
  current_step_index: number;
  created_at: string;
  completed_at?: string;
  summary?: string;
  error?: string;
}

export interface ApprovalRecord {
  id: string;
  task_id: string;
  tool_name: string;
  target: string;
  parameters: Record<string, unknown>;
  reason: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  created_at: string;
  expires_at: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: 'task_started' | 'tool_invoked' | 'approval_requested' | 'approval_decided' | 'task_completed' | 'security_alert';
  task_id?: string;
  tool_name?: string;
  summary: string;
  details?: Record<string, unknown>;
}
