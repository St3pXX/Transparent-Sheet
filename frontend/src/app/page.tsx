"use client";

import Topbar from "@/components/Topbar";
import Sidebar from "@/components/Sidebar";
import EntryBanner from "@/components/EntryBanner";
import AgentCard from "@/components/AgentCard";
import ReportCTA from "@/components/ReportCTA";
import HistoryView from "@/components/HistoryView";
import DataView from "@/components/DataView";
import SettingsView from "@/components/SettingsView";
import { useConsoleStore } from "@/lib/store";

export default function Home() {
  const { activeTab } = useConsoleStore();

  // 非任务 Tab：隐藏 Agent 看板，只显示对应内容
  if (activeTab !== "task") {
    return (
      <div className="min-h-screen bg-[--bg]">
        <Topbar />
        <div className="flex pt-[52px]">
          <Sidebar />
          <main className="flex-1 min-w-0">
            <div className="max-w-[1200px] mx-auto px-7 py-5">
              {activeTab === "history" && <HistoryView />}
              {activeTab === "data" && <DataView />}
              {activeTab === "settings" && <SettingsView />}
            </div>
          </main>
        </div>
      </div>
    );
  }

  // 任务 Tab：显示完整 Agent 看板
  return (
    <div className="min-h-screen bg-[--bg]">
      <Topbar />

      <div className="flex pt-[52px]">
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <div className="max-w-[1200px] mx-auto px-7 py-5 pb-10 flex flex-col gap-3.5">
            {/* Entry Banner */}
            <EntryBanner />

            {/* Three Agent Cards */}
            <div className="grid grid-cols-3 gap-3.5">
              <AgentCard type="review" />
              <AgentCard type="analysis" />
              <AgentCard type="risk" />
            </div>

            {/* Report CTA */}
            <ReportCTA />
          </div>
        </main>
      </div>
    </div>
  );
}
