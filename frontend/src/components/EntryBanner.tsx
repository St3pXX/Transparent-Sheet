"use client";

import { useConsoleStore } from "@/lib/store";

export default function EntryBanner() {
  const { agentStatus, recordIds } = useConsoleStore();

  const status = agentStatus["entry"];
  const output = agentStatus["entry"] ? "录入完成" : "等待执行";
  const count = recordIds.length;

  return (
    <div className="bg-[--s1] border border-[--bd] rounded-xl p-4 flex items-center justify-between">
      <div className="flex items-center gap-3.5">
        {/* Icon */}
        <div className="w-9 h-9 bg-[--blue-d] rounded-lg flex items-center justify-center flex-shrink-0">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4 text-[--blue]"
          >
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
          </svg>
        </div>
        <div>
          <div className="text-[15px] font-medium text-[--text]">Entry Agent</div>
          <div className="text-[11px] text-[--t3] font-mono mt-0.5">
            数据录入 · 前置依赖节点
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-5">
          <div className="text-center">
            <div className="text-[16px] font-medium text-[--text] tracking-[-0.3px]">
              {count > 0 ? count : "—"}
            </div>
            <div className="text-[10px] text-[--t3] font-mono uppercase tracking-wider mt-0.5">
              新增记录
            </div>
          </div>
          <div className="w-px h-6 bg-[--bd]" />
          <div className="text-center">
            <div className="text-[16px] font-medium text-[--text] tracking-[-0.3px]">
              {count > 0 ? "99.2%" : "—"}
            </div>
            <div className="text-[10px] text-[--t3] font-mono uppercase tracking-wider mt-0.5">
              完整率
            </div>
          </div>
          <div className="w-px h-6 bg-[--bd]" />
          <div className="text-center">
            <div className="text-[16px] font-medium text-[--text] tracking-[-0.3px]">
              ERP
            </div>
            <div className="text-[10px] text-[--t3] font-mono uppercase tracking-wider mt-0.5">
              数据源
            </div>
          </div>
        </div>

        {/* Status Badge */}
        {status === "success" && (
          <span className="text-[10.5px] font-mono px-2.5 py-1 rounded-full bg-[--green-d] text-[--green]">
            已完成
          </span>
        )}
        {status === "failed" && (
          <span className="text-[10.5px] font-mono px-2.5 py-1 rounded-full bg-[--red-d] text-[--red]">
            失败
          </span>
        )}
        {(!status || status === "running") && (
          <span className="text-[10.5px] font-mono px-2.5 py-1 rounded-full bg-[--blue-d] text-[--blue] animate-blink">
            进行中
          </span>
        )}
      </div>
    </div>
  );
}
