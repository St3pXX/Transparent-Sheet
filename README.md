# Transparent-Sheet

> 飞书多维表格上的多 Agent 虚拟运营团队

电商运营场景的多 Agent AI 协作平台，运行于飞书多维表格之上。通过多个 AI Agent 的透明化推理与协作，帮助运营团队完成数据补全、质量审核、销售分析、风险预警和汇报生成。

传统电商运营中，数据处理依赖人工逐条检查，效率低且易遗漏。TransparentSheet 将运营流程抽象为可编排的 Agent 流水线，让多个 AI Agent 并行处理不同维度的任务——补全缺失数据、评估数据质量、分析销售趋势、识别异常风险——最后汇总成结构化报告，等待人工确认后写入飞书表格，全程透明可追溯。

**核心设计原则：**
- 数据流与控制流分离 — State 只存引用，数据存 DataStore
- 所有变更经过人工确认 — 写入飞书前必须人工审批，防止 AI 幻觉导致数据错误
- 架构可替换 — DataStore 支持 SQLite / PostgreSQL / Turso，ConfirmationChannel 支持 Streamlit / Feishu Card

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 特性

- **透明化推理**：每个 Agent 的思考过程清晰可见，状态实时更新到前端
- **多 Agent 并行协作**：Entry Agent 串行执行入口任务，三节点（Review/Analysis/Risk）并行 fan-out，Report Agent 汇总结果
- **Human-in-loop 中断恢复**：执行流程在写入飞书前中断等待人工确认，支持 interrupt/resume
- **可扩展数据层**：DataStore 抽象接口，可从 SQLite 切换到 PostgreSQL/Turso
- **多渠道确认**：ConfirmationChannel 抽象，支持 Streamlit 或 Feishu Card 等不同 UI 渠道
- **状态持久化**：基于 LangGraph Checkpointer，支持断点续传和线程级恢复

## 架构

### Agent 执行流程

```
┌─────────────────────────────────────────────────────────┐
│                      Entry Agent                        │
│              解析用户输入，触发任务初始化                   │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│            Review / Analysis / Risk Agents              │  ◄── 并行 fan-out
│  Review: 补全数据质量评估   Analysis: 销售分析   Risk: 风险检测 │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│                     Report Agent                         │
│              汇总三节点输出，生成结构化报告                  │
└──────────────────────┬──────────────────────────────────┘
                       ▼
              [ 人工确认中断等待 ]
                       ▼
┌─────────────────────────────────────────────────────────┐
│                     Writeback                            │
│                    写入飞书多维表格                         │
└─────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 说明 |
|------|------|
| `agents/` | 6 个 Agent 定义：conductor（调度）、entry（入口）、review（审核）、analysis（分析）、risk（风险）、report（汇报） |
| `orchestration/` | LangGraph 图定义 + OrchestrationState（控制流） |
| `datastore/` | DataStore 抽象层 + SQLite 实现（数据存储） |
| `channels/` | ConfirmationChannel 抽象（确认渠道） |
| `config/` | LLM 配置（统一管理各 Agent 的模型初始化） |
| `feishu/` | 飞书 API 客户端（写入多维表格） |

### 技术栈

| 层级 | 技术 |
|------|------|
| Agent 编排 | LangGraph + LangChain + `create_react_agent` |
| LLM | OpenAI 兼容接口（DeepSeek / MiniMax / OpenAI） |
| 数据存储 | aiosqlite（异步 SQLite） |
| 前端框架 | Next.js 15 + App Router |
| 样式 | Tailwind CSS |
| 状态管理 | Zustand |
| 实时通信 | Server-Sent Events（SSE） |
| 飞书集成 | Feishu SDK |

## 项目结构

```
transparent-sheet/
├── agents/                     # 6 个 Agent + tools
│   ├── conductor.py            # Orchestration 调度 Agent
│   ├── entry.py                # 入口 Agent，解析用户输入
│   ├── review.py               # 审核 Agent，数据质量评估
│   ├── analysis.py             # 分析 Agent，销售数据分析
│   ├── risk.py                 # 风险 Agent，风险检测
│   ├── report.py               # 汇报 Agent，汇总生成报告
│   ├── wrappers.py             # Agent 工具包装器
│   └── tools/
│       ├── demo_data.py        # Demo 数据生成工具
│       └── datastore.py        # DataStore 操作工具
├── orchestration/
│   ├── graph.py                # LangGraph 图定义
│   ├── state.py                # OrchestrationState（控制流）
│   └── writeback.py            # 飞书写入节点
├── datastore/
│   ├── interfaces.py          # DataStore 抽象接口
│   ├── base.py                # 基础实现
│   └── sqlite.py              # SQLite 异步实现
├── channels/
│   ├── base.py                # ConfirmationChannel 抽象
│   ├── factory.py             # 渠道工厂
│   └── streamlit.py           # Streamlit 确认渠道
├── config/
│   └── llm.py                # LLM 配置（统一管理模型初始化）
├── feishu/
│   ├── client.py              # 飞书 API 客户端
│   └── exceptions.py          # 飞书异常定义
├── frontend/                   # Next.js 15 前端
│   ├── src/
│   │   ├── app/              # App Router 页面
│   │   ├── components/        # UI 组件
│   │   ├── lib/              # Zustand store + SSE hook
│   │   └── types/            # TypeScript 类型
│   └── package.json
└── tests/                     # 单元测试

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/St3pXX/Transparent-Sheet.git
cd Transparent-Sheet
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Keys
```

### 3. 安装后端依赖

```bash
cd transparent-sheet
pip install -e .
```

### 4. 启动前端

```bash
cd transparent-sheet/frontend
npm install
npm run dev
```

## 开发

### 运行测试

```bash
cd transparent-sheet
pytest
```

### 技术细节

详见 [docs/](docs/) 目录下的架构文档和设计规格。

## 当前阶段

**Phase 1-6**：核心流程全部打通 🎉

- ✅ Graph 执行（LangGraph + MemorySaver Checkpointer）
- ✅ 6 个 Agent 单元测试全部通过（15 passed）
- ✅ 前端 Next.js + 后端 FastAPI + SSE 流式交互
- ✅ Streamlit 控制台可独立运行
- ✅ Next.js rewrite 代理 SSE 到 FastAPI
- ✅ 前端 Browser UI 端到端验证（部分）
- ✅ **DeepSeek LLM 集成**（deepseek-chat，真实 AI 推理）
- ✅ **飞书多维表格写入**（自动创建字段 + batch_create，实测 20 条记录写入成功）

后续计划：
- Phase 5: Streamlit UX 改进 + FeishuCardChannel
- Phase 6: ~~Feishu 正式集成~~ ✅ **已完成**
- Phase 7: 开源准备（PostgreSQL/Turso 替换）

## License

MIT
