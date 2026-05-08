"use client";

import { useConsoleStore } from "@/lib/store";

const TABS = [
  { key: "task", label: "任务" },
  { key: "history", label: "历史" },
  { key: "data", label: "数据" },
  { key: "settings", label: "设置" },
] as const;

export default function Topbar() {
  const { activeTab, setActiveTab } = useConsoleStore();

  return (
    <header className="fixed inset-0 h-[52px] bg-black/75 backdrop-blur-xl border-b border-[--bd] flex items-center justify-between px-6 z-50">
      {/* Left */}
      <div className="flex items-center gap-6">
        <span className="text-[15px] font-medium text-[--text] tracking-[-0.3px]">
          Transparent<span className="text-[--blue]">Sheet</span>
        </span>
        <nav className="flex gap-0.5">
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-3.5 py-1.5 text-[13px] rounded-md transition-all ${
                activeTab === key
                  ? "text-[--text] bg-[--s1]"
                  : "text-[--t2] hover:text-[--text] hover:bg-[--s1]"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3.5">
        <span className="text-[11.5px] text-[--t3] font-mono">
          <span className="inline-block w-1.5 h-1.5 bg-[--green] rounded-full mr-1.5 align-middle animate-blink" />
          就绪 · v2.0
        </span>
      </div>
    </header>
  );
}
