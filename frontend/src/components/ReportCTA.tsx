"use client";

import { useConsoleStore } from "@/lib/store";
import { useTaskStream } from "@/lib/sse";

const LEVEL_STYLES: Record<string, string> = {
  red: "text-[--red]",
  orange: "text-[--orange]",
  yellow: "text-[--t3]",
  default: "text-[--t2]",
};

function SuggestionItem({ item }: { item: { item: string; type: string } }) {
  const level = item.type?.toLowerCase() || "default";
  const color = LEVEL_STYLES[level] || LEVEL_STYLES["default"];
  const label = level === "red" ? "紧急" : level === "orange" ? "次要" : level === "yellow" ? "关注" : "建议";

  return (
    <div className="text-[13.5px] text-[--t2] leading-[1.85]">
      <strong className={color}>{label}</strong>
      {" — "}{item.item}
    </div>
  );
}

export default function ReportCTA() {
  const { reportContent, pendingConfirmations, taskStatus, taskId } = useConsoleStore();
  const { confirmTask } = useTaskStream();

  const isConfirming = taskStatus === "confirming";
  const isDone = taskStatus === "done";

  // Show only when we have something real to show
  if (!isConfirming && !isDone && !reportContent) return null;

  const summary = reportContent
    ? reportContent.slice(0, 400)
    : "等待报告生成...";

  const handleConfirm = async () => {
    if (!taskId) return;
    await confirmTask(taskId, "confirm");
  };

  const handleReset = () => {
    const { resetTask } = useConsoleStore.getState();
    resetTask();
  };

  return (
    <div className="bg-[--s1] border border-[--bd] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-[--bd] flex items-center justify-between bg-gradient-to-r from-[--blue-d] to-transparent">
        <div className="flex items-center gap-3.5">
          <div className="w-9 h-9 bg-[--blue-d] border border-[--blue]/20 rounded-lg flex items-center justify-center">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-4 h-4 text-[--blue]"
            >
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14,2 14,8 20,8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10,9 9,9 8,9" />
            </svg>
          </div>
          <div>
            <div className="text-[15px] font-medium text-[--text]">Report Agent</div>
            <div className="text-[11px] text-[--t3] font-mono mt-0.5">
              报告生成 · 需要您确认后写入飞书表格
            </div>
          </div>
        </div>
        <span className="text-[11px] font-mono px-3 py-1 rounded-full bg-[--blue-d] text-[--blue] animate-blink">
          {isDone ? "已完成" : "待确认"}
        </span>
      </div>

      {/* Body */}
      <div className="px-6 py-5 grid grid-cols-[1fr_1fr_auto] gap-6 items-start">
        {/* Summary */}
        <div>
          <div className="text-[10.5px] font-medium text-[--t3] uppercase tracking-wider mb-2.5">
            执行摘要
          </div>
          <div className="text-[13.5px] text-[--t2] leading-[1.85]">
            {summary}
            {reportContent && reportContent.length >= 400 && (
              <span className="text-[--t3]">...</span>
            )}
          </div>
        </div>

        {/* Suggestions from pendingConfirmations */}
        <div>
          <div className="text-[10.5px] font-medium text-[--t3] uppercase tracking-wider mb-2.5">
            处理建议
          </div>
          <div className="flex flex-col gap-3">
            {pendingConfirmations.length > 0 ? (
              pendingConfirmations.map((c, i) => (
                <SuggestionItem key={i} item={c} />
              ))
            ) : (
              <div className="text-[13.5px] text-[--t3] italic">
                等待处理建议生成...
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 pl-6 border-l border-[--bd] justify-center">
          {isConfirming && (
            <button
              className="px-6 py-2.5 bg-[--blue] border-none rounded-lg text-[13.5px] font-medium text-white cursor-pointer hover:opacity-85 transition-opacity whitespace-nowrap"
              onClick={handleConfirm}
            >
              确认写入
            </button>
          )}
          {isDone && (
            <button
              className="px-6 py-2.5 bg-[--green-d] border border-[--green]/20 rounded-lg text-[13.5px] font-medium text-[--green] cursor-pointer whitespace-nowrap"
              disabled
            >
              已写入
            </button>
          )}
          <button
            className="px-6 py-2.5 bg-transparent border border-[--bd] rounded-lg text-[13.5px] text-[--t2] cursor-pointer hover:bg-[--s2] hover:text-[--text] transition-all whitespace-nowrap disabled:opacity-50"
            onClick={handleReset}
            disabled={taskStatus === "running"}
          >
            重新开始
          </button>
        </div>
      </div>
    </div>
  );
}
