# TransparentSheet 文档

> 飞书多维表格上的多 Agent 虚拟运营团队文档中心

## 文档结构

```
docs/
├── index.md                          # 文档总览（本文）
├── specs/                            # 设计规格文档
│   ├── 2026-04-30-transparentsheet-design.md   # 主设计文档
│   └── console-preview.html          # 控制台 UI 预览 Spec
├── architecture/                     # 架构文档
│   ├── overview.md                   # 架构总览
│   ├── agent-roles.md                # Agent 职责矩阵
│   ├── data-store.md                 # DataStore 抽象层设计
│   └── confirmation-flow.md          # Human-in-loop 确认流程
├── guides/                           # 开发/使用指南
│   ├── getting-started.md            # 快速开始（Next.js + FastAPI）
│   └── console-guide.md              # 控制台使用指南
└── adrs/                             # 架构决策记录 (Architecture Decision Records)
    ├── 001-use-langgraph.md          # 采用 LangGraph 作为编排框架
    ├── 002-async-sqlite.md           # 使用 aiosqlite 而非同步 sqlite3
    └── 003-confirmation-channel.md   # ConfirmationChannel 抽象
```

## 项目概览

**TransparentSheet** 是一个运行在飞书多维表格上的多 Agent 协作平台，通过多个 AI Agent 的透明化协作，帮助电商运营人员完成数据管理、分析、预警、汇报。

- **核心框架**：LangGraph + LangChain
- **数据存储**：aiosqlite（异步 SQLite）
- **前端**：Next.js 15 + Tailwind CSS（Phase 1-4 原型）
- **后端 API**：FastAPI + SSE（LangGraph 包装层）
- **飞书集成**：Feishu SDK
- **当前阶段**：Phase 1-4（控制台模式 Demo）

## 源码结构

```
transparent-sheet/           # Python 后端（LangGraph Agent 编排）
├── agents/                 # 6 个 Agent 定义
├── orchestration/          # Graph + State
├── datastore/              # 抽象层 + SQLite 实现
├── channels/               # ConfirmationChannel 抽象
├── console/                # 旧 Streamlit 控制台（保留）
└── feishu/                 # 飞书 API 客户端

backend/                    # FastAPI SSE 网关（新建）
├── server.py               # SSE 端点，包装 LangGraph
└── requirements.txt

frontend/                   # Next.js 15 前端（新建）
├── src/
│   ├── app/               # App Router 页面
│   ├── components/        # UI 组件
│   ├── lib/               # Zustand store + SSE hook
│   └── types/             # TypeScript 类型
├── tailwind.config.ts
└── package.json
```

## 快速链接

- [设计规格文档](specs/2026-04-30-transparentsheet-design.md)
- [控制台 UI 预览](specs/console-preview.html)
- [架构总览](architecture/overview.md)
- [快速开始（指南）](guides/getting-started.md)
- [前端/后端开发指南](guides/getting-started.md)
