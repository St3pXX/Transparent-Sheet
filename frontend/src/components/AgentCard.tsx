"use client";

import type { AgentStatus } from "@/types";
import { useConsoleStore } from "@/lib/store";

type AgentType = "review" | "analysis" | "risk";

const AGENT_META = {
  review: {
    name: "Review Agent",
    role: "数据审核 · 并行节点",
    iconBg: "bg-[--green-d]",
    iconColor: "text-[--green]",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
        <path d="M9 11l3 3L22 4" />
        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
      </svg>
    ),
  },
  analysis: {
    name: "Analysis Agent",
    role: "趋势分析 · 并行节点",
    iconBg: "bg-[--blue-d]",
    iconColor: "text-[--blue]",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
        <line x1="2" y1="20" x2="22" y2="20" />
      </svg>
    ),
  },
  risk: {
    name: "Risk Agent",
    role: "风险预警 · 并行节点",
    iconBg: "bg-[--orange-d]",
    iconColor: "text-[--orange]",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
  },
};

function StatusBadge({ status }: { status: AgentStatus | undefined }) {
  if (status === "success")
    return <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[--green-d] text-[--green]">完成</span>;
  if (status === "failed")
    return <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[--red-d] text-[--red]">失败</span>;
  if (status === "running")
    return <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[--blue-d] text-[--blue] animate-blink">进行中</span>;
  return <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[--s3] text-[--t3]">等待</span>;
}

// ---- Review Content (real data from agent_outputs["review"]) ----
function ReviewContent({ output }: { output: string }) {
  if (!output) {
    return (
      <div className="text-[12px] text-[--t3] italic">等待数据审核结果...</div>
    );
  }
  return (
    <div className="text-[12px] text-[--t2] whitespace-pre-wrap leading-relaxed">
      {output.slice(0, 500)}
      {output.length > 500 && <span className="text-[--t3]">...</span>}
    </div>
  );
}

// ---- Analysis Content (real data from analysis_summary + KPI parsing) ----
function parseAnalysisOutput(summary: string): { sales: string; orders: string; aov: string; repurchase: string; insight: string } | null {
  if (!summary) return null;
  // 尝试从 summary 中提取关键指标
  const salesMatch = summary.match(/销售额[：:]\s*([¥\$\d.\w万]+)/);
  const ordersMatch = summary.match(/订单[数：:]\s*(\d+)/);
  const aovMatch = summary.match(/客单价[：:]\s*([¥\$\d.\w]+)/);
  const repurchaseMatch = summary.match(/复购率[：:]\s*([\d.]+%)/);
  const insightMatch = summary.match(/建议[：:](.+)/) || summary.match(/(?:分析|结论)[：:](.+)/) || summary.match(/(.+)/);

  return {
    sales: salesMatch ? salesMatch[1] : "—",
    orders: ordersMatch ? ordersMatch[1] : "—",
    aov: aovMatch ? aovMatch[1] : "—",
    repurchase: repurchaseMatch ? repurchaseMatch[1] : "—",
    insight: insightMatch ? insightMatch[1].trim() : summary.slice(0, 80),
  };
}

function AnalysisContent({ summary }: { summary: string }) {
  const data = parseAnalysisOutput(summary);

  if (!data) {
    return <div className="text-[12px] text-[--t3] italic">等待销售分析结果...</div>;
  }

  return (
    <div>
      <div className="grid grid-cols-2 gap-1.5 mb-3">
        {[
          { label: "销售额", value: data.sales },
          { label: "订单数", value: data.orders },
          { label: "客单价", value: data.aov },
          { label: "复购率", value: data.repurchase },
        ].map(({ label, value }) => (
          <div key={label} className="bg-[--s2] border border-[--bd] rounded-lg p-2.5">
            <div className="text-[10px] text-[--t3] uppercase tracking-wider">{label}</div>
            <div className="text-[17px] font-medium text-[--text] tracking-[-0.3px] mt-1">{value}</div>
          </div>
        ))}
      </div>
      {data.insight && (
        <div className="border-l-2 border-[--blue] rounded-r-lg bg-[--s2] px-3 py-2 text-[12px] text-[--t2] leading-relaxed">
          {data.insight}
        </div>
      )}
    </div>
  );
}

// ---- Risk Content (real data from risk_levels) ----
function RiskContent({ riskLevels }: { riskLevels: Record<string, string> }) {
  const entries = Object.entries(riskLevels);

  if (entries.length === 0) {
    return <div className="text-[12px] text-[--t3] italic">等待风险检测结果...</div>;
  }

  const highCount = entries.filter(([, l]) => l === "high").length;
  const medCount = entries.filter(([, l]) => l === "medium").length;
  const lowCount = entries.filter(([, l]) => l === "low").length;

  return (
    <div>
      <div className="flex flex-col gap-1.5 mb-2.5">
        {entries.map(([id, level]) => (
          <div key={id} className="bg-[--s2] border border-[--bd] rounded-lg p-2.5 flex items-center gap-2.5">
            <span
              className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                level === "high"
                  ? "bg-[--red] shadow-[0_0_5px_rgba(255,69,58,0.7)]"
                  : level === "medium"
                  ? "bg-[--orange]"
                  : "bg-[--green]"
              }`}
            />
            <div className="flex-1">
              <div className="text-[12px] text-[--t2] line-clamp-1">
                {level === "high" ? "高风险记录" : level === "medium" ? "中风险记录" : "低风险记录"}
              </div>
              <div className="text-[10px] font-mono text-[--t3] mt-0.5">{id}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="bg-[--s2] border border-[--bd] rounded-lg p-2.5 text-[11px] text-[--t3] leading-relaxed">
        综合评分：高风险 <strong className="text-[--t2]">{highCount}</strong> 项 · 中风险{" "}
        <strong className="text-[--t2]">{medCount}</strong> 项 · 低风险{" "}
        <strong className="text-[--t2]">{lowCount}</strong> 项
      </div>
    </div>
  );
}

export default function AgentCard({ type }: { type: AgentType }) {
  const { agentStatus, agentOutputs, riskLevels, analysisSummary } = useConsoleStore();
  const meta = AGENT_META[type];
  const status = agentStatus[type];

  return (
    <div className="bg-[--s1] border border-[--bd] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[--bd] flex items-center gap-2.5">
        <div className={`w-7 h-7 ${meta.iconBg} rounded-lg flex items-center justify-center flex-shrink-0`}>
          <span className={meta.iconColor}>{meta.icon}</span>
        </div>
        <div>
          <div className="text-[13px] font-medium text-[--text]">{meta.name}</div>
          <div className="text-[10.5px] text-[--t3] mt-0.5">{meta.role}</div>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Body */}
      <div className="p-3.5">
        {type === "review" && <ReviewContent output={agentOutputs["review"] || ""} />}
        {type === "analysis" && <AnalysisContent summary={analysisSummary} />}
        {type === "risk" && <RiskContent riskLevels={riskLevels} />}
      </div>
    </div>
  );
}
