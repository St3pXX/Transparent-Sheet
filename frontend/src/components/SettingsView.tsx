"use client";

import { useConsoleStore } from "@/lib/store";

export default function SettingsView() {
  const { agentStatus } = useConsoleStore();

  const AGENT_ITEMS = [
    { key: "entry", label: "Entry Agent", desc: "数据录入", color: "blue" },
    { key: "review", label: "Review Agent", desc: "数据审核", color: "green" },
    { key: "analysis", label: "Analysis Agent", desc: "趋势分析", color: "blue" },
    { key: "risk", label: "Risk Agent", desc: "风险预警", color: "orange" },
    { key: "report", label: "Report Agent", desc: "报告生成", color: "t2" },
  ];

  const STATUS_COLOR: Record<string, string> = {
    success: "bg-[--green-d] text-[--green]",
    failed: "bg-[--red-d] text-[--red]",
    running: "bg-[--blue-d] text-[--blue]",
    idle: "bg-[--s3] text-[--t3]",
  };

  const STATUS_LABEL: Record<string, string> = {
    success: "就绪",
    failed: "失败",
    running: "运行中",
    idle: "空闲",
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Page Title */}
      <div>
        <h1 className="text-[18px] font-semibold text-[--text]">系统设置</h1>
        <p className="text-[12px] text-[--t3] mt-0.5">配置 LLM、数据源和 Agent 参数</p>
      </div>

      {/* LLM Settings */}
      <div className="bg-[--s1] border border-[--bd] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[--bd]">
          <span className="text-[13px] font-medium text-[--text]">LLM 配置</span>
        </div>
        <div className="p-4 flex flex-col gap-3">
          {[
            { label: "模型", value: "MiniMax-M2.5" },
            { label: "Base URL", value: "http://67.230.168.254:8080/v1" },
            { label: "Temperature", value: "0.5" },
            { label: "最大迭代", value: "10 步" },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between py-1.5">
              <span className="text-[12px] text-[--t2]">{label}</span>
              <span className="text-[12px] font-mono text-[--text] bg-[--s2] px-2.5 py-1 rounded-md">
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Status */}
      <div className="bg-[--s1] border border-[--bd] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[--bd]">
          <span className="text-[13px] font-medium text-[--text]">Agent 状态</span>
        </div>
        <div className="p-4 grid grid-cols-5 gap-3">
          {AGENT_ITEMS.map(({ key, label, desc }) => {
            const status = agentStatus?.[key] || "idle";
            return (
              <div key={key} className="bg-[--s2] border border-[--bd] rounded-xl p-3 text-center">
                <div className="text-[11px] font-medium text-[--text]">{label}</div>
                <div className="text-[10px] text-[--t3] mt-0.5">{desc}</div>
                <span className={`inline-block mt-2 text-[10px] font-mono px-2 py-0.5 rounded-full ${STATUS_COLOR[status]}`}>
                  {STATUS_LABEL[status]}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Data Source */}
      <div className="bg-[--s1] border border-[--bd] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[--bd]">
          <span className="text-[13px] font-medium text-[--text]">飞书数据源</span>
        </div>
        <div className="p-4 flex flex-col gap-3">
          {[
            { label: "App ID", value: "cli_a971b57ffd3adcd5", secret: false },
            { label: "App Secret", value: "PVOb7fYEIZvVvT8uDkCkeeEKyzrxy6PM", secret: true },
            { label: "Bitable Token", value: "M5mVb7WeuaMLJxsNqp0cKGxEnmg", secret: false },
            { label: "Table ID", value: "tblWPpB6focdTHy0", secret: false },
          ].map(({ label, value, secret }) => (
            <div key={label} className="flex items-center justify-between py-1.5">
              <span className="text-[12px] text-[--t2]">{label}</span>
              <span className="text-[12px] font-mono text-[--text] bg-[--s2] px-2.5 py-1 rounded-md">
                {secret ? "••••••••" : value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Version */}
      <div className="text-center text-[11px] text-[--t3]">
        TransparentSheet v2.0 · 构建于 Next.js 15 + FastAPI + LangGraph
      </div>
    </div>
  );
}
