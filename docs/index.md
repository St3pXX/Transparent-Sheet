# TransparentSheet 文档

> 飞书多维表格上的多 Agent 虚拟运营团队文档中心

## 文档结构

```
docs/
├── index.md                          # 文档总览（本文）
├── superpowers/specs/                # 设计规格文档
│   └── 2026-04-30-transparentsheet-design.md   # 主设计文档
├── architecture/                     # 架构文档
│   ├── overview.md                   # 架构总览
│   ├── agent-roles.md                # Agent 职责矩阵
│   ├── data-store.md                 # DataStore 抽象层设计
│   └── confirmation-flow.md          # Human-in-loop 确认流程
├── guides/                           # 开发/使用指南
│   ├── getting-started.md            # 快速开始
│   └── console-guide.md              # 控制台使用指南
└── adrs/                             # 架构决策记录 (ADRs)
    ├── 001-use-langgraph.md          # 采用 LangGraph 作为编排框架
    ├── 002-async-sqlite.md           # 使用 aiosqlite 而非同步 sqlite3
    └── 003-confirmation-channel.md   # ConfirmationChannel 抽象
```

## 项目概览

**TransparentSheet** 是一个运行在飞书多维表格上的多 Agent 协作平台，通过多个 AI Agent 的透明化协作，帮助电商运营人员完成数据管理、分析、预警、汇报。

- **核心框架**：LangGraph + LangChain
- **数据存储**：aiosqlite（异步 SQLite）+ SqliteSaver 持久化 Checkpointer
- **后端 API**：FastAPI + SSE（LangGraph 包装层，含纯 HTML 控制台）
- **前端**：Next.js 15 + Tailwind CSS + Zustand
- **飞书集成**：Feishu SDK（lark-oapi）
- **当前阶段**：Phase 1-6 全部完成，测试 28/28 通过

## 源码结构

```
transparent-sheet/
├── agents/                     # 6 个 Agent 定义
│   ├── conductor.py / entry.py / review.py / analysis.py / risk.py / report.py
│   ├── wrappers.py             # Node Wrapper（隔离 create_react_agent 与全局 State）
│   └── tools/                  # DemoDataProvider + DataStore 操作工具
├── orchestration/
│   ├── graph.py                # LangGraph 图定义（error_handler 已接入）
│   ├── state.py                # OrchestrationState（控制流）
│   └── writeback.py            # 飞书写入节点
├── datastore/
│   ├── interfaces.py / base.py # DataStore 抽象层
│   ├── sqlite.py               # SQLite 异步实现（默认）
│   ├── postgres.py             # PostgreSQL 实现（asyncpg）
│   ├── turso.py                # Turso/libSQL 实现
│   └── factory.py              # 后端工厂（环境变量切换）
├── channels/
│   ├── base.py                 # ConfirmationChannel 抽象
│   ├── factory.py              # 渠道工厂
│   └── streamlit.py            # Streamlit 确认渠道
├── api/
│   └── server.py               # FastAPI SSE 后端 + 纯 HTML 控制台
├── config/
│   └── llm.py                  # LLM 配置（统一管理模型初始化）
├── feishu/
│   ├── client.py               # 飞书 API 客户端（令牌桶限流 + 自动字段创建）
│   └── exceptions.py           # 飞书异常定义
├── console/
│   └── console.html            # 纯 HTML 控制台页面
├── frontend/                   # Next.js 15 前端（可选，完整 UI）
│   └── src/ ...
└── tests/                      # 单元 + 集成测试（24 passed）
```

## 快速链接

- [设计规格文档](superpowers/specs/2026-04-30-transparentsheet-design.md)
- [架构总览](architecture/overview.md)
- [快速开始（指南）](guides/getting-started.md)
- [控制台使用指南](guides/console-guide.md)
