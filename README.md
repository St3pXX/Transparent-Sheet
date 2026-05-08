# TransparentSheet

> 飞书多维表格上的多 Agent 虚拟运营团队

电商运营场景的多 Agent 协作平台，通过 AI Agent 的透明化推理与协作，完成数据管理、分析、预警、汇报。

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 特性

- **透明化推理**：每个 Agent 的思考过程清晰可见
- **多 Agent 协作**：Entry → Review/Analysis/Risk 并行 → Report → 人工确认 → 写入飞书
- **Human-in-loop**：关键节点需人工确认，保证数据安全
- **可扩展架构**：DataStore、ConfirmationChannel 抽象层设计

## 架构

```
Entry Agent ──►  ┌─► Review Agent  ──┐
                 ├──► Analysis Agent ──┤
                 └──► Risk Agent  ─────┘ ──► Report Agent ──► 人工确认 ──► 飞书写入
```

**技术栈：**

- **后端**：Python + LangGraph + LangChain + aiosqlite
- **前端**：Next.js 15 + Tailwind CSS + TypeScript + Zustand
- **集成**：Feishu SDK

## 项目结构

```
transparent-sheet/
├── agents/                 # 6 个 Agent（conductor, entry, review, analysis, risk, report）
│   └── tools/              # demo_data, datastore 工具
├── orchestration/           # Graph + State编排
├── datastore/              # 抽象层 + SQLite 实现
├── channels/               # ConfirmationChannel 抽象
├── config/                 # LLM 配置
├── feishu/                 # 飞书 API 客户端
├── console/                # Streamlit 控制台（保留）
├── frontend/               # Next.js 15 前端
└── tests/                  # 单元测试
```

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

**Phase 1-4**：控制台模式 Demo，核心逻辑开发中。

后续计划：
- Phase 5: Streamlit UX 改进
- Phase 6: Feishu 正式集成
- Phase 7: 开源准备（PostgreSQL/Turso 替换）

## License

MIT
