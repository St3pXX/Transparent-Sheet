"use client";

import { useConsoleStore } from "@/lib/store";

export default function DataView() {
  const { recordIds, anomalyRecordIds, agentStatus, agentOutputs } = useConsoleStore();

  const agentEntryStatus = agentStatus?.entry;
  const hasData = recordIds.length > 0;

  return (
    <div className="flex flex-col gap-3">
      {/* Page Title */}
      <div>
        <h1 className="text-[18px] font-semibold text-[--text]">数据管理</h1>
        <p className="text-[12px] text-[--t3] mt-0.5">查看已录入的飞书多维表格数据</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "录入记录总数", value: recordIds.length || "—", colorVar: "--blue" },
          { label: "异常记录数", value: anomalyRecordIds.length || "0", colorVar: "--orange" },
          { label: "审核状态", value: agentEntryStatus === "success" ? "通过" : "—", colorVar: "--green" },
          { label: "数据源", value: "飞书 Bitable", colorVar: "--t2" },
        ].map(({ label, value, colorVar }) => (
          <div key={label} className="bg-[--s1] border border-[--bd] rounded-xl p-4">
            <div className="text-[10.5px] text-[--t3] uppercase tracking-wider">{label}</div>
            <div className={`text-[22px] font-semibold mt-1`} style={{ color: `var(${colorVar})` }}>
              {value}
            </div>
          </div>
        ))}
      </div>

      {/* Record IDs */}
      <div className="bg-[--s1] border border-[--bd] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[--bd] flex items-center justify-between">
          <span className="text-[13px] font-medium text-[--text]">已录入记录 ID</span>
          <span className="text-[11px] font-mono text-[--t3]">{recordIds.length} 条</span>
        </div>

        {hasData ? (
          <div className="p-4">
            <div className="grid grid-cols-2 gap-2">
              {recordIds.map((id, i) => (
                <div
                  key={id}
                  className="bg-[--s2] border border-[--bd] rounded-lg px-3 py-2 flex items-center gap-2"
                >
                  <span className="text-[10px] font-mono text-[--t3] w-6">#{i + 1}</span>
                  <span className="text-[11px] font-mono text-[--text] truncate">{id}</span>
                  <span
                    className={`ml-auto w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                      anomalyRecordIds.includes(id) ? "bg-[--orange]" : "bg-[--green]"
                    }`}
                  />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="text-[32px] mb-3">📋</div>
            <div className="text-[13px] text-[--t2]">暂无数据</div>
            <div className="text-[11px] text-[--t3] mt-1">
              执行任务后，数据将显示在这里
            </div>
          </div>
        )}
      </div>

      {/* Bitable Config */}
      <div className="bg-[--s1] border border-[--bd] rounded-xl p-4">
        <div className="text-[13px] font-medium text-[--text] mb-3">飞书连接配置</div>
        <div className="grid grid-cols-2 gap-3 text-[12px]">
          {[
            { label: "App Token", value: "M5mVb7WeuaMLJxsNqp0cKGxEnmg" },
            { label: "Table ID", value: "tblWPpB6focdTHy0" },
          ].map(({ label, value }) => (
            <div key={label} className="bg-[--s2] border border-[--bd] rounded-lg p-3">
              <div className="text-[10px] text-[--t3] mb-1">{label}</div>
              <div className="text-[12px] font-mono text-[--text]">{value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
