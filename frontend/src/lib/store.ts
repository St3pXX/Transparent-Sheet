import { create } from "zustand";
import type {
  TaskState,
  AgentStatus,
  AgentOutputs,
  RiskLevels,
  HistoryItem,
} from "@/types";

type ActiveTab = "task" | "history" | "data" | "settings";

interface ConsoleStore {
  // Tab 导航
  activeTab: ActiveTab;

  // 任务状态
  taskId: string | null;
  taskInput: string;
  taskStatus: "idle" | "running" | "confirming" | "done" | "error";

  // Agent 实时状态
  agentStatus: Record<string, AgentStatus>;
  agentOutputs: AgentOutputs;
  recordIds: string[];
  anomalyRecordIds: string[];
  riskLevels: RiskLevels;
  analysisSummary: string;
  reportContent: string;
  pendingConfirmations: { item: string; type: string }[];

  // 历史记录
  history: HistoryItem[];

  // Actions
  setTaskInput: (input: string) => void;
  setActiveTab: (tab: ActiveTab) => void;
  startTask: (taskId: string, input: string) => void;
  updateState: (state: Partial<TaskState>) => void;
  setTaskStatus: (status: "idle" | "running" | "confirming" | "done" | "error") => void;
  addHistoryItem: (item: HistoryItem) => void;
  resetTask: () => void;
}

export const useConsoleStore = create<ConsoleStore>((set) => ({
  activeTab: "task",
  taskId: null,
  taskInput: "",
  taskStatus: "idle",
  agentStatus: {},
  agentOutputs: {},
  recordIds: [],
  anomalyRecordIds: [],
  riskLevels: {},
  analysisSummary: "",
  reportContent: "",
  pendingConfirmations: [],
  history: [],

  setTaskInput: (input) => set({ taskInput: input }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  startTask: (taskId, input) =>
    set({
      taskId,
      taskInput: input,
      taskStatus: "running",
      agentStatus: {},
      agentOutputs: {},
      recordIds: [],
      anomalyRecordIds: [],
      riskLevels: {},
      analysisSummary: "",
      reportContent: "",
      pendingConfirmations: [],
    }),

  updateState: (state) =>
    set((s) => {
      // Update running history item to completed when done
      const history =
        s.taskId && state.status === "completed"
          ? s.history.map((item) =>
              item.id === s.taskId ? { ...item, status: "completed" as const } : item
            )
          : s.history;

      return {
        agentStatus: { ...s.agentStatus, ...(state.agent_status || {}) },
        agentOutputs: { ...s.agentOutputs, ...(state.agent_outputs || {}) },
        recordIds: state.record_ids || s.recordIds,
        anomalyRecordIds: state.anomaly_record_ids || s.anomalyRecordIds,
        riskLevels: { ...s.riskLevels, ...(state.risk_levels || {}) },
        analysisSummary: state.analysis_summary || s.analysisSummary,
        reportContent: state.report_content || s.reportContent,
        pendingConfirmations: state.pending_confirmations || s.pendingConfirmations,
        taskStatus:
          state.status === "awaiting_confirm"
            ? "confirming"
            : state.status === "completed"
            ? "done"
            : s.taskStatus,
        history,
      };
    }),

  setTaskStatus: (status) => set({ taskStatus: status }),

  addHistoryItem: (item) =>
    set((s) => ({
      history: [item, ...s.history].slice(0, 10),
    })),

  resetTask: () =>
    set({
      taskId: null,
      taskStatus: "idle",
      agentStatus: {},
      agentOutputs: {},
      recordIds: [],
      anomalyRecordIds: [],
      riskLevels: {},
      analysisSummary: "",
      reportContent: "",
      pendingConfirmations: [],
    }),
}));
