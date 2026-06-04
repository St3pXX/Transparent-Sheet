# TransparentSheet 快速开始

## 环境要求

- Python >= 3.12
- Node.js 18+（可选，仅 Next.js 前端需要）

## 安装

### 1. Python 后端（LangGraph Agent 编排 + FastAPI）

```bash
git clone https://github.com/St3pXX/Transparent-Sheet.git
cd Transparent-Sheet
pip install -e .
```

### 2. Next.js 前端（可选）

```bash
cd frontend
npm install
```

## 配置

复制 `.env.example` 为 `.env`，填入 LLM 和飞书配置：

```bash
cp .env.example .env
```

必需的环境变量：
- `OPENAI_API_KEY` — DeepSeek / OpenAI API Key
- `OPENAI_BASE_URL` — 默认 `https://api.deepseek.com/v1`
- `OPENAI_MODEL` — 默认 `deepseek-chat`

飞书写入（可选，Demo 模式不需要）：
- `FEISHU_APP_ID` / `FEISHU_APP_SECRET`
- `FEISHU_BITABLE_APP_TOKEN` / `FEISHU_BITABLE_TABLE_ID`

## 启动

### 方式一：HTML 控制台（推荐，无额外依赖）

```bash
python -m uvicorn transparent_sheet.api.server:app --host 0.0.0.0 --port 8000
```

打开 http://localhost:8000

### 方式二：Next.js 前端（完整 UI）

需要两个终端：

```bash
# 终端 1：启动 FastAPI 后端
python -m uvicorn transparent_sheet.api.server:app --host 0.0.0.0 --port 8000

# 终端 2：启动 Next.js 前端
cd frontend
npm run dev
```

打开 http://localhost:3001

## Demo 模式

不配置飞书时，系统使用内置 Demo 数据生成器，可以完整体验所有 Agent 协作流程。

## 项目结构

```
transparent-sheet/
├── agents/                 # 6 个 Agent 定义
├── orchestration/          # Graph + State + Writeback
├── datastore/              # DataStore 抽象 + SQLite
├── channels/               # ConfirmationChannel 抽象
├── api/
│   └── server.py           # FastAPI SSE 后端 + HTML 控制台
├── config/                 # LLM 配置
├── feishu/                 # 飞书 API 客户端
├── console/
│   └── console.html        # 纯 HTML 控制台页面
├── frontend/               # Next.js 15 前端（可选）
└── tests/                  # 测试（24 passed）
```

## 运行测试

```bash
pytest tests/
```
