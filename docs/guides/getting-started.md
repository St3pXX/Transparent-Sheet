# TransparentSheet 快速开始

## 环境要求

- Python >= 3.11
- Node.js 18+
- npm

## 安装

### 1. Python 后端（LangGraph Agent 编排）

```bash
cd transparent-sheet
pip install -e . --no-deps                    # 仅安装包，跳过 feishu 等可选依赖
pip install -r ../backend/requirements.txt   # FastAPI + SSE 依赖
```

### 2. Next.js 前端

```bash
cd frontend
npm install
```

## 配置

复制 `.env.example` 为 `.env`，填入飞书配置（可选，Demo 模式不需要）：

```bash
cp .env.example .env
```

## 启动

需要两个终端：

```bash
# 终端 1：启动 FastAPI SSE 后端（端口 8000）
cd transparent-sheet
uvicorn backend.server:app --port 8000 --reload

# 终端 2：启动 Next.js 前端（端口 3000）
cd frontend
npm run dev
```

打开 http://localhost:3000

## Streamlit 控制台（旧）

旧的 Streamlit 控制台仍可使用，但已被 Next.js 前端替代：

```bash
cd transparent-sheet
streamlit run console/app.py
```

## Demo 模式

不配置飞书时，系统使用内置 Demo 数据生成器，可以完整体验所有 Agent 协作流程。

## 项目结构

```
transparent-sheet/           # Python 后端
├── agents/                 # 6 个 Agent 定义
├── orchestration/          # Graph + State
├── datastore/             # SQLiteDataStore
├── channels/              # ConfirmationChannel 抽象
├── console/               # 旧 Streamlit 控制台
└── feishu/                # 飞书 API 客户端

backend/                    # FastAPI SSE 网关
├── server.py               # /stream/{task_id} SSE 端点
└── requirements.txt        # fastapi, uvicorn, sse-starlette

frontend/                   # Next.js 15 前端
├── src/
│   ├── app/               # page.tsx, layout.tsx, globals.css
│   ├── components/        # Topbar, Sidebar, EntryBanner, AgentCard, ReportCTA
│   ├── lib/               # Zustand store, SSE hook
│   └── types/             # TypeScript 类型
└── tailwind.config.ts
```

## SSE 数据流

```
浏览器 (Next.js)
    │ EventSource /fetch POST
    ▼
FastAPI backend/server.py
    │ graph.astream_events()
    ▼
LangGraph Orchestrator (transparent-sheet)
    │ 按 node_name 分轨推送
    ▼
浏览器 SSE 事件 → Zustand store → React 组件更新
```

## 运行测试

```bash
cd transparent-sheet
pytest tests/
```
