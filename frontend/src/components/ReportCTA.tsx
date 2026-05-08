"use client";

import { useConsoleStore } from "@/lib/store";
import { useTaskStream } from "@/lib/sse";

export default function ReportCTA() {
  const { reportContent, pendingConfirmations, taskStatus, taskId } = useConsoleStore();
  const { confirmTask } = useTaskStream();

  const isConfirming = taskStatus === "confirming" || taskStatus === "done";

  if (!isConfirming && !reportContent) return null;

  const summary = reportContent
    ? reportContent.slice(0, 300)
    : "本周（04/21-04/27）运营数据已补录完成。共录入 847 笔订单，涵盖 5 个品类，销售额达 ¥128.6 万，较上周环比 +12.3%，整体运营态势良好。审核发现 2 条异常数据（已标注），风控识别高风险项目 1 项，需优先处理。";

  const suggestions = [
    { level: "red", label: "紧急", text: "商品A（SKU-2024-001）库存仅剩 23 件，预计 3 天内售罄，建议立即补货。" },
    { level: "orange", label: "次要", text: "商品B价格波动异常，请核实近期调价记录。" },
    { level: "t3", label: "关注", text: "物流延迟订单共 5 笔，建议主动联系客户说明情况，降低投诉风险。" },
  ];

  const handleConfirm = async () => {
    if (!taskId) return;
    await confirmTask(taskId, "confirm");
  };

  const handleRevise = async () => {
    if (!taskId) return;
    await confirmTask(taskId, "revise");
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
          {taskStatus === "done" ? "已完成" : "待确认"}
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
            {summary.length >= 300 && "..."}
          </div>
        </div>

        {/* Suggestions */}
        <div>
          <div className="text-[10.5px] font-medium text-[--t3] uppercase tracking-wider mb-2.5">
            处理建议
          </div>
          <div className="flex flex-col gap-3">
            {suggestions.map(({ level, label, text }) => (
              <div key={label} className="text-[13.5px] text-[--t2] leading-[1.85]">
                <strong style={{ color: level === "red" ? "var(--red)" : level === "orange" ? "var(--orange)" : "var(--t3)" }}>
                  {label}
                </strong>
                {" — "}{text}
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 pl-6 border-l border-[--bd] justify-center">
          <button
            className="px-6 py-2.5 bg-[--blue] border-none rounded-lg text-[13.5px] font-medium text-white cursor-pointer hover:opacity-85 transition-opacity whitespace-nowrap disabled:opacity-50"
            onClick={handleConfirm}
            disabled={taskStatus === "done"}
          >
            确认写入
          </button>
          <button
            className="px-6 py-2.5 bg-transparent border border-[--bd] rounded-lg text-[13.5px] text-[--t2] cursor-pointer hover:bg-[--s2] hover:text-[--text] transition-all whitespace-nowrap disabled:opacity-50"
            onClick={handleRevise}
            disabled={taskStatus === "done"}
          >
            修改报告
          </button>
        </div>
      </div>
    </div>
  );
}
