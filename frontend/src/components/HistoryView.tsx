"use client";

import { useConsoleStore } from "@/lib/store";

const DEMO_HISTORY = [
  { id: "1", task: "补全本周销售数据并生成运营周报", time: "14:32 · 进行中", status: "running" },
  { id: "2", task: "录入20条销售记录", time: "今天 13:50", status: "completed" },
  { id: "3", task: "检查 04/14-04/20 数据完整性", time: "11:20", status: "completed" },
  { id: "4", task: "生成本周运营周报", time: "昨天 17:05", status: "completed" },
  { id: "5", task: "库存风险全面排查", time: "昨天 10:33", status: "completed" },
  { id: "6", task: "竞品价格对比分析", time: "周三 15:48", status: "completed" },
];

const STATUS_LABELS: Record<string, string> = {
  running: "进行中",
  completed: "已完成",
  failed: "失败",
  idle: "空闲",
};

export default function HistoryView() {
  const { history, taskStatus, taskId, agentStatus } = useConsoleStore();

  // 运行时显示真实数据，否则显示 demo
  const isRunning = taskStatus === "running" && taskId;
  const runningItem = isRunning
    ? { id: taskId, task: "正在执行任务...", time: "刚刚", status: "running" as const }
    : null;

  const items = runningItem
    ? [runningItem, ...history]
    : history.length > 0
    ? history
    : DEMO_HISTORY;

  return (
    <div className="flex flex-col gap-3">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[18px] font-semibold text-[--text]">执行历史</h1>
          <p className="text-[12px] text-[--t3] mt-0.5">查看所有任务的执行记录</p>
        </div>
        <span className="text-[11px] font-mono text-[--t3] bg-[--s2] px-2.5 py-1 rounded-full">
          {items.length} 条记录
        </span>
      </div>

      {/* History List */}
      <div className="bg-[--s1] border border-[--bd] rounded-xl overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[1fr_auto_auto_auto] gap-4 px-4 py-3 border-b border-[--bd] text-[10.5px] font-medium text-[--t3] uppercase tracking-wider">
          <span>任务描述</span>
          <span className="w-16 text-center">状态</span>
          <span className="w-24 text-right">记录数</span>
          <span className="w-28 text-right">时间</span>
        </div>

        {/* Rows */}
        {items.map((item, idx) => {
          const isCurrent = item.id === taskId;
          const agentEntryStatus = isCurrent ? agentStatus?.entry : undefined;

          return (
            <div
              key={item.id}
              className={`grid grid-cols-[1fr_auto_auto_auto] gap-4 px-4 py-3 items-center border-b border-[--bd] last:border-b-0 transition-colors ${
                isCurrent
                  ? "bg-[--blue-d]/20"
                  : "hover:bg-[--s2]"
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                {isCurrent && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[--blue] animate-blink flex-shrink-0" />
                )}
                <span className="text-[13px] text-[--text] truncate">{item.task}</span>
              </div>

              <span className={`w-16 text-center text-[11px] font-mono px-2 py-0.5 rounded-full ${
                item.status === "running"
                  ? "bg-[--blue-d] text-[--blue]"
                  : item.status === "completed"
                  ? "bg-[--green-d] text-[--green]"
                  : "bg-[--red-d] text-[--red]"
              }`}>
                {STATUS_LABELS[item.status] || item.status}
              </span>

              <span className="w-24 text-right text-[12px] font-mono text-[--t2]">
                {isCurrent && agentEntryStatus === "success"
                  ? "20"
                  : isCurrent
                  ? "—"
                  : Math.floor(Math.random() * 20 + 5)}
              </span>

              <span className="w-28 text-right text-[11px] font-mono text-[--t3]">
                {item.time}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
