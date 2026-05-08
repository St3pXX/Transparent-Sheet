# TransparentSheet 架构总览

## 系统架构图

```
┌──────────────────────────────────────────────────────────────┐
│               Next.js + Tailwind CSS 控制台                    │
│  ┌──────────┬──────────┬──────────┬──────────┬────────┐    │
│  │ 侧边栏   │ Entry    │ Review   │ Analysis │ Risk   │    │
│  │ 任务输入  │ Banner   │ AgentCard│ AgentCard│ AgentCard│  │
│  └──────────┴──────────┴──────────┴──────────┴────────┘    │
│              ReportCTA (确认/修改)                            │
└─────────────────────────┬────────────────────────────────────┘
                          │ SSE / POST
┌─────────────────────────▼────────────────────────────────────┐
│           FastAPI SSE 后端 (backend/server.py)                  │
│  /stream/{task_id}  ←  graph.astream_events()                │
│  /confirm/{task_id}  ←  graph.update_state()                 │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│               LangGraph Orchestrator                         │
│               (transparent-sheet/)                            │
│               interrupt_before="writeback_node"               │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│               DataStore (aiosqlite)                            │
└──────────────────────────────────────────────────────────────┘

## Graph 拓扑

```
START
  ↓
orchestration_node (理解任务、拆解、路由)
  ↓
entry_node (数据录入，前置依赖)
  ↓
┌─────────────────────────────────────────┐
│        并行执行（共享 record_ids）          │
│   review_node    analysis_node    risk_node │
└─────────────────────────────────────────┘
  ↓
report_node (生成报告 + pending_confirmations)
  ↓
finish_report_node (中断点)
  ↓
(interrupt_before="writeback_node")
  ↓
┌─────────────────────────────────────────┐
│    ConfirmationChannel (外部处理)         │
│    - StreamlitChannel (Phase 1-4)        │
│    - FeishuCardChannel (Phase 5)        │
└─────────────────────────────────────────┘
  ↓
[用户确认 → writeback_node]
[用户调整 → revise_report_node → writeback_node]
  ↓
END
```

## 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | Next.js 15 + Tailwind CSS | 控制台 UI，Phase 1-4 原型 |
| 后端 API | FastAPI + SSE | LangGraph 包装，SSE 流式推送 |
| Agent 编排 | LangGraph + LangChain | 核心框架 |
| 链路追踪 | LangSmith | 开发调试 |
| 飞书接入 | Feishu SDK (Python) | 多维表格 API |
| 数据存储 | aiosqlite | 异步数据流存储 + Checkpointer |
| 存储抽象 | 抽象基类 | PostgreSQL / Turso 可替换 |
| 旧控制台 | Streamlit | 保留，Phase 1-4 备选 |
| 流式输出 | SSE + graph.astream_events() | 实时分轨展示 |
| 限流 | 令牌桶 + asyncio | FeishuApiClient 底层 |

## 系统数据流

```
┌──────────────────────────────────────────────────────┐
│           Next.js 前端 (localhost:3000)               │
│  Sidebar → AgentCard → ReportCTA (Zustand 状态管理)    │
└──────────────────┬───────────────────────────────────┘
                   │ SSE / POST confirm
┌──────────────────▼───────────────────────────────────┐
│           FastAPI SSE 后端 (localhost:8000)             │
│  /stream/{task_id}  →  graph.astream_events()         │
│  /confirm/{task_id} →  graph.update_state() + stream  │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│           LangGraph Orchestrator                       │
│  (transparent-sheet/orchestration/graph.py)           │
│  interrupt_before="writeback_node"                    │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│                      DataStore                         │
│              (SQLiteDataStore / 抽象基类)              │
└───────────────────────────────────────────────────────┘

## 数据与控制流分离

```
┌──────────────────────────────────────────────────────────┐
│  LangGraph State（控制流）                                  │
│  只存：task_id, user_id, record_ids, status, 摘要         │
│  大小：< 1KB / 任务                                        │
└──────────────────────────────────────────────────────────┘
                         ↕ (通过 record_id 关联)
┌──────────────────────────────────────────────────────────┐
│  DataStore（数据流，抽象接口）                               │
│  - save_records / get_records                             │
│  - save_agent_output / get_agent_output                   │
│  - save_confirmation                                      │
└──────────────────────────────────────────────────────────┘
```

## Agent 职责

| Agent | 角色 | 输出 |
|-------|------|------|
| Orchestra Conductor | 调度 | intent + sub_tasks |
| Entry Agent | 数据员 | record_ids |
| Review Agent | 审核 | anomaly_record_ids |
| Analysis Agent | 分析师 | analysis_summary |
| Risk Agent | 风控 | risk_levels |
| Report Agent | 秘书 | report_content + pending_confirmations |

## 核心设计原则

1. **透明化推理** — 每个 Agent 执行过程分轨可见
2. **串出并行拓扑** — Entry 串行 + Review/Analysis/Risk 并行
3. **数据/控制流分离** — State 只存引用，数据存 DataStore
4. **部分失败容错** — Agent 独立状态标记，失败不阻塞全流程
5. **中断与恢复** — Checkpointer 持久化 + thread_id 隔离
6. **双入口架构** — ConfirmationChannel 抽象，Streamlit/FastAPI+Next.js 可替换
7. **前后端分离** — FastAPI SSE 网关解耦 LangGraph 与前端框架
