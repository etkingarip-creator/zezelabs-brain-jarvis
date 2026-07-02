// ── Agent Types ─────────────────────────────────────────────────────────────

export type AgentStatus = 'online' | 'offline' | 'busy' | 'error' | 'idle';

export interface AgentInfo {
  name: string;
  role: string;
  status: AgentStatus;
  tokens: number;
}

export interface AgentTask {
  id: string;
  agentName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: string;
  completedAt?: string;
  result?: string;
  error?: string;
}

// ── Department Types ────────────────────────────────────────────────────────

export type DepartmentName =
  | 'zeze_business'
  | 'zeze_comms'
  | 'zeze_compliance'
  | 'zeze_dev'
  | 'zeze_ops'
  | 'zeze_production'
  | 'zeze_design'
  | 'zeze_trend'
  | 'app_factory'
  | 'crypto_trading'
  | 'zeze_game'
  | 'zeze_aro'
  | 'zeze_rnd'
  | 'zeze_sec'
  | 'media_factory'
  | 'zeze_betting'
  | 'zeze_academy';

export type FloorType = 'executive' | 'office' | 'meeting' | 'tech' | 'gym';

export interface DepartmentAudit {
  rabbitmq_connection: 'connected' | 'disconnected' | 'unknown';
  config_status: 'valid' | 'invalid' | 'missing';
  issues: string[];
  workload: 'low' | 'medium' | 'high' | 'critical';
  telemetry_source?: string;
}

export interface SystemUsage {
  cpu: string;
  ram: string;
  gpu: string;
}

export interface DepartmentStatus {
  status: 'healthy' | 'degraded' | 'down' | 'unknown' | 'offline';
  activity?: 'working' | 'queued' | 'idle';  // canlı aktivite
  current_task?: string | null;              // şu an ne yapıyor (canlı)
  last_active?: string | null;
  completed?: number;
  uptime: string;
  api_calls: number;
  success_rate: string;
  queue_depth: number;
  system_usage: SystemUsage;
  active_agents: number;
  agents_list: AgentInfo[];
  audit: DepartmentAudit;
  telemetry_note?: string;
}

export interface AllDepartmentsResponse {
  departments: Record<DepartmentName, DepartmentStatus>;
  brain_online: boolean;
  brain_model?: string | null;
  fetched_at: string;
}

export interface FloorMeta {
  id: number;
  name: string;
  type: FloorType;
  departmentId: DepartmentName;
  description: string;
}

// ── API Response Types ──────────────────────────────────────────────────────

export interface HealthResponse {
  status: 'ok' | 'error' | 'degraded';
  version?: string;
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  status: 'success' | 'error';
  model?: string;
  tokens_used?: number;
}

export interface RuntimeStatusResponse {
  status: string;
  ai_mode: string;
  version: string;
}

export interface LogsResponse {
  lines: string[];
}

// ── WebSocket Message Types ─────────────────────────────────────────────────

export type WsMessageType =
  | 'state'
  | 'transcript'
  | 'response'
  | 'volume'
  | 'brain_status'
  | 'stats'
  | 'command'
  | 'mic_toggle'
  | 'voice_toggle';

export interface WsMessage {
  type: WsMessageType;
  val?: unknown;
  id?: string;
  model?: string;
  cpu?: number;
  memory?: number;
  uptime?: string;
}

// ── UI State Types ──────────────────────────────────────────────────────────

export type JarvisState = 'idle' | 'listening' | 'thinking' | 'speaking';
export type ConnectionMode = 'websocket' | 'rest' | 'offline';

export interface ChatAttachment {
  name: string;
  type: string;
  url: string;
  size: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'jarvis';
  text: string;
  timestamp: number;
  taskId?: string;
  departmentId?: string;
  attachments?: ChatAttachment[];
  action?: {
    id: string;
    type: 'command' | 'write_file' | 'git_push';
    target: string;
    description: string;
    status: 'pending' | 'executing' | 'success' | 'failed' | 'rejected';
    output?: string;
  };
}

export interface SystemStats {
  cpu: number;
  memory: number;
  uptime: string;
}

export interface BrainStatus {
  val: string;
  model?: string;
}

// ── Workspace Modular Layout Types ──────────────────────────────────────────

export interface WorkspaceModule {
  id: string; // departmentId
  size: 'small' | 'medium' | 'large';
}

export type WorkspacePreset = 'default' | 'research' | 'finance' | 'security' | 'custom';

