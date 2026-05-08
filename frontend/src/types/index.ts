export type AgentName =
  | "entry"
  | "review"
  | "analysis"
  | "risk"
  | "report";

export type AgentStatus = "success" | "failed" | "skipped" | "running";

export type RiskLevel = "high" | "medium" | "low";

export type TaskStatus =
  | "pending"
  | "running"
  | "awaiting_confirm"
  | "completed"
  | "error";

export interface AgentOutputs {
  [agent: string]: string;
}

export interface AgentStatusMap {
  [agent: string]: AgentStatus;
}

export interface RiskLevels {
  [recordId: string]: RiskLevel;
}

export interface PendingConfirmation {
  item: string;
  type: string;
}

export interface TaskState {
  task_id: string;
  user_id: string;
  task: string;
  intent: string;
  sub_tasks: string[];
  record_ids: string[];
  anomaly_record_ids: string[];
  agent_status: AgentStatusMap;
  agent_outputs: AgentOutputs;
  risk_levels: RiskLevels;
  analysis_summary: string;
  report_content: string;
  original_report: string;
  pending_confirmations: PendingConfirmation[];
  confirmed: boolean;
  confirmed_modifications: unknown[];
  status: TaskStatus;
  error: string | null;
}

export type SSEEventType = "state" | "confirm_required" | "waiting_confirm" | "continuation" | "done" | "error";

export interface SSEEvent {
  type: SSEEventType;
  node?: string | null;
  status?: TaskStatus;
  data: Partial<TaskState> | TaskState | null;
}

export interface HistoryItem {
  id: string;
  task: string;
  time: string;
  status: "running" | "completed" | "pending";
}
