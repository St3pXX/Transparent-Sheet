"use client";

import { useConsoleStore } from "@/lib/store";
import { useTaskStream } from "@/lib/sse";
import { useState } from "react";
import type { HistoryItem } from "@/types";

const DEMO_HISTORY: HistoryItem[] = [
  { id: "1", task: "补全本周销售数据并生成运营周报", time: "14:32 · 进行中", status: "running" },
  { id: "2", task: "检查 04/14-04/20 数据完整性", time: "11:20 · 已完成", status: "completed" },
  { id: "3", task: "生成本周运营周报", time: "昨天 17:05", status: "completed" },
  { id: "4", task: "库存风险全面排查", time: "昨天 10:33", status: "completed" },
  { id: "5", task: "竞品价格对比分析", time: "周三 15:48", status: "completed" },
];

export default function Sidebar() {
  const { taskInput, setTaskInput, taskStatus, history } = useConsoleStore();
  const { startStream } = useTaskStream();
  const [localInput, setLocalInput] = useState("");

  const displayHistory: HistoryItem[] = history.length > 0 ? history : DEMO_HISTORY;

  const handleRun = () => {
    const input = localInput.trim() || taskInput;
    if (!input) return;
    const taskId = crypto.randomUUID();
    startStream(taskId, input);
  };

  return (
    <aside className="w-[252px] bg-[--s1] border-r border-[--bd] flex flex-col sticky top-[52px] h-[calc(100vh-52px)] overflow-hidden">
      {/* Top: Task Input */}
      <div className="p-4 pb-0 flex-shrink-0">
        <div className="text-[10.5px] font-medium text-[--t3] uppercase tracking-wider mb-2">
          指令
        </div>
        <textarea
          className="w-full min-h-[82px] bg-[--s2] border border-[--bd] rounded-lg p-3 text-[13px] text-[--text] resize-none outline-none focus:border-[--blue] transition-colors leading-relaxed placeholder:text-[--t3]"
          placeholder="描述任务目标..."
          value={localInput}
          onChange={(e) => setLocalInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              handleRun();
            }
          }}
        />
        <button
          className="w-full mt-2 py-2.5 bg-[--blue] border-none rounded-lg text-[13px] font-medium text-white cursor-pointer hover:opacity-85 transition-opacity disabled:opacity-50"
          onClick={handleRun}
          disabled={taskStatus === "running"}
        >
          {taskStatus === "running" ? "执行中..." : "执行任务"}
        </button>
      </div>

      {/* Bottom: History */}
      <div className="flex-1 overflow-y-auto p-4 pb-5">
        <div className="text-[10.5px] font-medium text-[--t3] uppercase tracking-wider mb-2">
          最近
        </div>
        <div className="flex flex-col gap-0.5">
          {displayHistory.map((item) => (
            <button
              key={item.id}
              className={`text-left p-2.5 rounded-lg border transition-all ${
                item.status === "running"
                  ? "bg-[--s2] border-[--bd]"
                  : "border-transparent hover:bg-[--s2]"
              }`}
              onClick={() => setLocalInput(item.task)}
            >
              <div className="text-[10px] font-mono text-[--t3] mb-1">
                {item.time}
              </div>
              <div className="text-[12px] text-[--t2] leading-snug line-clamp-2">
                {item.task}
              </div>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
