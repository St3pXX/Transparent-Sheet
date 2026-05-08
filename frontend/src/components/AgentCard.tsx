"use client";

import type { AgentStatus } from "@/types";
import { useConsoleStore } from "@/lib/store";

type AgentType = "review" | "analysis" | "risk";

interface AgentCardProps {
  type: AgentType;
}

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

function ReviewContent({ output }: { output: string }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="bg-[--s2] border border-[--bd] rounded-lg p-2.5">
        <div className="flex justify-between mb-1">
          <span className="text-[10.5px] font-mono text-[--t3]">REC_042</span>
          <span className="text-[10px] font-mono text-[--orange]">异常</span>
        </div>
        <div className="text-[12px] text-[--t2] leading-snug">
          数量字段为负值（-3），已标记待处理
        </div>
      </div>
      <div className="bg-[--s2] border border-[--bd] rounded-lg p-2.5">
        <div className="flex justify-between mb-1">
          <span className="text-[10.5px] font-mono text-[--t3]">REC_019</span>
          <span className="text-[10px] font-mono text-[--orange]">异常</span>
        </div>
        <div className="text-[12px] text-[--t2] leading-snug">
          价格字段缺失，已用均值填充
        </div>
      </div>
      <div className="bg-[--s2] border border-[--bd] rounded-lg p-2.5">
        <div className="flex justify-between mb-1">
          <span className="text-[10.5px] font-mono text-[--t3]">其余 845 条</span>
          <span className="text-[10px] font-mono text-[--green]">合规</span>
        </div>
        <div className="text-[12px] text-[--t2] leading-snug">
          字段完整率 98.3%，超过校验阈值（95%）
        </div>
      </div>
    </div>
  );
}

function AnalysisContent({ output }: { output: string }) {
  return (
    <div>
      {/* KPI Grid */}
      <div className="grid grid-cols-2 gap-1.5 mb-3">
        {[
          { label: "销售额", value: "¥128.6万", delta: "+12.3%", up: true },
          { label: "订单数", value: "847", delta: "+8.7%", up: true },
          { label: "客单价", value: "¥1,518", delta: "-2.1%", up: false },
          { label: "复购率", value: "23.4%", delta: "+1.8%", up: true },
        ].map(({ label, value, delta, up }) => (
          <div key={label} className="bg-[--s2] border border-[--bd] rounded-lg p-2.5">
            <div className="text-[10px] text-[--t3] uppercase tracking-wider">{label}</div>
            <div className="text-[17px] font-medium text-[--text] tracking-[-0.3px] mt-1">
              {value}
            </div>
            <div className={`text-[10px] font-mono mt-0.5 ${up ? "text-[--green]" : "text-[--red]"}`}>
              {delta}
            </div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="h-[50px] mb-3">
        <svg viewBox="0 0 200 50" preserveAspectRatio="none" className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0a84ff" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#0a84ff" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path
            d="M0,42 L18,38 L36,33 L54,27 L72,30 L90,22 L108,17 L126,13 L144,10 L162,12 L180,7 L200,2 L200,50 L0,50 Z"
            fill="url(#cg)"
          />
          <path
            d="M0,42 L18,38 L36,33 L54,27 L72,30 L90,22 L108,17 L126,13 L144,10 L162,12 L180,7 L200,2"
            fill="none"
            stroke="#0a84ff"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <circle cx="200" cy="2" r="2.5" fill="#0a84ff" />
        </svg>
      </div>

      {/* Insight */}
      <div className="border-l-2 border-[--blue] rounded-r-lg bg-[--s2] px-3 py-2 text-[12px] text-[--t2] leading-relaxed">
        周末促销效果显著，04/25-26 销量环比 +23%；客单价下降可能与折扣套餐推广相关，建议关注定价策略。
      </div>
    </div>
  );
}

function RiskContent({ riskLevels }: { riskLevels: Record<string, string> }) {
  const items = [
    { id: "REC_042", level: "high", text: "商品A库存严重不足（剩余23件）", sub: "高风险" },
    { id: "REC_019", level: "medium", text: "商品B价格异常波动（±15%）", sub: "中风险" },
    { id: "REC_031", level: "low", text: "物流延迟预警（5笔订单）", sub: "低风险" },
    { id: "REC_055", level: "low", text: "客户投诉风险升高", sub: "低风险" },
  ];

  const highCount = items.filter((i) => i.level === "high").length;
  const medCount = items.filter((i) => i.level === "medium").length;
  const lowCount = items.filter((i) => i.level === "low").length;

  return (
    <div>
      <div className="flex flex-col gap-1.5 mb-2.5">
        {items.map((item) => (
          <div key={item.id} className="bg-[--s2] border border-[--bd] rounded-lg p-2.5 flex items-center gap-2.5">
            <span
              className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                item.level === "high"
                  ? "bg-[--red] shadow-[0_0_5px_rgba(255,69,58,0.7)]"
                  : item.level === "medium"
                  ? "bg-[--orange]"
                  : "bg-[--green]"
              }`}
            />
            <div className="flex-1">
              <div className="text-[12px] text-[--t2]">{item.text}</div>
              <div className="text-[10px] font-mono text-[--t3] mt-0.5">{item.id} · {item.sub}</div>
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

export default function AgentCard({ type }: AgentCardProps) {
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
        {type === "analysis" && <AnalysisContent output={analysisSummary} />}
        {type === "risk" && <RiskContent riskLevels={riskLevels} />}
      </div>
    </div>
  );
}
