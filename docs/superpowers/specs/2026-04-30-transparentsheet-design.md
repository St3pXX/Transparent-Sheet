# TransparentSheet — 多维表格多智能体虚拟组织

> 飞书多维表格上的多 Agent 虚拟运营团队，让 AI Agent 像真实团队成员一样各司其职、互相协作。

**文档版本：** 1.1
**创建日期：** 2026-04-30
**更新日期：** 2026-04-30
**状态：** 设计阶段

---

## 一、项目定位

### 1.1 一句话定位

TransparentSheet 是一个运行在飞书多维表格上的多 Agent 协作平台，通过多个 AI Agent 的透明化协作，帮助电商运营人员完成数据管理、分析、预警、汇报。

### 1.2 核心价值

- **透明化推理**：每个 Agent 的执行过程可见，打破 AI 黑盒
- **虚拟团队**：多个 Agent 各司其职，模拟真实运营团队的协作
- **双入口**：聊天 + 表格按钮，兼顾通用和效率
- **Human-in-loop**：用户确认/调整，形成反馈闭环

### 1.3 目标用户

- 电商运营团队（数据管理、分析、汇报）
- 中小企业管理多维表格数据
- 对 AI Agent 协作感兴趣的个人开发者

---

## 二、业务流程

### 2.1 标准执行流程（修正后）

```
用户发指令
    ↓
Orchestra Conductor 理解任务、拆解子任务
    ↓
Entry Agent 补录/清洗数据（前置依赖，必须先完成）
    ↓
┌──────────────────────────────────────────────┐
│        3 个 Agent 并行执行（串出并行）         │
│  ┌───────┐  ┌───────┐  ┌───────┐  │
│  │Review │  │Analysis│  │ Risk  │  │
│  │ Agent │  │ Agent │  │ Agent │  │
│  └───────┘  └───────┘  └───────┘  │
└──────────────────────────────────────────────┘
    ↓
Report Agent 汇总结果、生成报告
    ↓
Graph 挂起（interrupt_after="report_node"）
    ↓
用户确认/调整（Human-in-loop）
    ↓
写入飞书多维表格
```

> ⚠️ **关键修正**：Entry Agent 是所有下游的前置依赖，必须串行先完成。并行只发生在 Review、Analysis、Risk 三个 Agent 之间。

### 2.2 电商运营 Demo 场景

| 任务类型 | 示例指令 | 触发 Agent |
|---------|---------|-----------|
| 数据补录 | "补全本周销售数据" | Entry Agent |
| 数据审核 | "检查数据完整性" | Review Agent |
| 数据分析 | "分析本周销售趋势" | Analysis Agent |
| 风险预警 | "检查库存和异常" | Risk Agent |
| 周报生成 | "生成本周运营周报" | Report Agent |

---

## 三、Agent 架构

### 3.1 Agent 职责矩阵

| Agent | 角色 | 核心能力 | 输出 |
|-------|------|---------|------|
| **Orchestra Conductor** | 调度 | 意图理解、任务拆解、路由分发 | 任务执行计划 |
| **Entry Agent** | 数据员 | 数据采集、格式转换、模拟数据生成 | record_ids（写入的记录 ID 列表） |
| **Review Agent** | 审核 | 完整性检查、规则校验、异常标注 | 审核报告 + 异常 record_ids |
| **Analysis Agent** | 分析师 | 统计分析、趋势计算、摘要生成 | 数据分析结论 |
| **Risk Agent** | 风控 | 异常检测、风险评级、预警触发 | 风险清单 + 预警级别 |
| **Report Agent** | 秘书 | 报告生成、周报撰写、建议输出 | 格式化报告 + 待确认项 |

### 3.2 Orchestrator 状态机设计（修正后）

> ⚠️ **关键修正**：State 只传控制流信息（IDs、状态、摘要），不传全量业务数据。避免 Context Window 爆炸。

```python
class OrchestrationState(TypedDict):
    task_id: str                         # 任务唯一 ID（UUID）
    task: str                            # 用户原始任务描述
    intent: str                          # 理解后的意图
    sub_tasks: list[str]                 # 拆解后的子任务列表
    record_ids: list[str]                # 飞书表格 Record IDs（Entry 写入后）
    anomaly_record_ids: list[str]        # 审核发现的异常 Record IDs
    risk_levels: dict[str, str]          # record_id → risk_level (high/medium/low)
    analysis_summary: str                # 分析结论摘要
    report_content: str                  # 报告内容
    pending_confirmations: list[dict]  # 待用户确认项
    confirmed: bool                     # 用户是否已确认
    status: str                        # pending/running/awaiting_confirm/completed
    error: str | None                   # 错误信息

class DataStore:
    """数据与控制流分离：全量数据存 SQLite，State 只存引用"""
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
    def save_table_records(self, task_id: str, records: list[dict]): ...
    def get_records(self, task_id: str, record_ids: list[str]): ...
    def save_agent_output(self, task_id: str, agent: str, output: dict): ...
    def get_agent_output(self, task_id: str, agent: str): ...
    def save_confirmation(self, task_id: str, confirmed_data: dict): ...
```

### 3.3 Graph 节点与边（修正后）

```
START
  ↓
orchestration_node (理解任务、拆解、路由)
  ↓
entry_node (仅当需要数据补录时触发)
  ↓
┌─────────────────────────────────────────┐
│   review_node ←→ analysis_node ←→ risk_node
│        (三个节点并行，共享 record_ids)
└─────────────────────────────────────────┘
  ↓
report_node
  ↓
(interrupt_after="report_node")
  ↓
human_confirm_node (Graph 挂起，等待用户确认)
  ↓
[用户调整 → report_node] 或 [用户确认 → writeback_node]
  ↓
writeback_node (写入飞书表格)
  ↓
END

条件边逻辑：
- orchestration_node → entry_node (当需要数据录入时)
- orchestration_node → [review_node, analysis_node, risk_node] (当数据已存在时，跳过 entry)
- entry_node → [review_node, analysis_node, risk_node] (固定串出并行)
- review_node + analysis_node + risk_node → report_node (汇合)
```

---

## 四、技术架构

### 4.1 数据与控制流分离原则

```
┌──────────────────────────────────────────────────────────┐
│  LangGraph State（控制流）                                  │
│  只存：task_id, record_ids, status, 摘要, flag             │
│  大小：< 1KB / 任务                                        │
└──────────────────────────────────────────────────────────┘
                         ↕ (通过 record_id 关联)
┌──────────────────────────────────────────────────────────┐
│  SQLite（数据流）                                           │
│  存：全量表格内容、Agent 中间输出、用户确认数据              │
│  大小：无限制                                              │
└──────────────────────────────────────────────────────────┘
```

> 每个 Agent 通过 Tool 持有 DataStore 引用，用 record_id 查询实际数据，而非从 State/Prompt 中读取全量内容。

### 4.2 阶段一：控制台模式（修正后）

```
┌──────────────────────────────────────────────────────────────────┐
│                     Streamlit 控制台（看板布局）                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐     │
│  │  任务输入 │  Entry   │  Review  │ Analysis │ Risk+Report │     │
│  │  (左侧)  │  面板    │  面板    │  面板    │   面板      │     │
│  │          │  分轨    │  分轨    │  分轨    │   分轨      │     │
│  │          │  SSE     │  SSE     │  SSE     │   SSE       │     │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                     LangGraph Orchestrator
                     (配置 interrupt_after="report_node")
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      SQLite（数据存储层）                          │
│  - 表格全量内容                                                   │
│  - 各 Agent 中间输出                                              │
│  - 用户确认记录                                                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌────────────────────────┐
                    │   FeishuApiClient      │
                    │   (限流 + 重试 + 队列) │
                    └────────────────────────┘
                              ↓
                    飞书多维表格（展示层）
```

### 4.3 FeishuApiClient 限流设计

```python
class FeishuApiClient:
    """统一的飞书 API 客户端，封装限流和重试"""

    def __init__(self, app_id: str, app_secret: str, qps: int = 20):
        self._rate_limiter = TokenBucketRateLimiter(qps=qps)
        self._semaphore = asyncio.Semaphore(10)  # 最大并发 10

    async def get_table_records(self, table_id: str, record_ids: list[str]):
        """带令牌桶限流的批量读取"""
        async with self._semaphore:
            await self._rate_limiter.acquire()
            return await self._request(...)

    async def batch_create_records(self, table_id: str, records: list[dict]):
        """分批写入，避免触发 429"""
        BATCH_SIZE = 10
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            await self._rate_limiter.acquire()
            await self._request(...)  # 重试逻辑：429 时指数退避
```

> 限流参数：QPS=20（保守值），最大并发=10，写入批次大小=10，429 时退避重试。

### 4.4 Human-in-loop：Checkpointer 实现

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 初始化 Checkpointer
checkpointer = SqliteSaver.from_conn_string(":memory:")

# 编译 Graph，配置中断点
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_after="report_node"  # report_node 执行后挂起
)

# 执行流程
# Step 1: 运行到 report_node，Graph 自动挂起
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
for event in graph.stream(user_input, config, stream_mode="values"):
    if event.get("status") == "awaiting_confirm":
        break  # Graph 已挂起，等待用户确认

# Step 2: Streamlit 渲染确认卡片
render_confirmation_ui(event)

# Step 3: 用户确认后，恢复执行
graph.update_state(config, {"confirmed": True})
for event in graph.stream(None, config):
    ...  # 继续执行 writeback_node
```

### 4.5 Streamlit 分轨展示（看板模式）

```python
# 3 列分轨布局
left_col, entry_col, review_col, analysis_col = st.columns([1, 1, 1, 1])
bottom_row = st.columns([1, 1])

# 每个面板订阅对应 Agent 的 SSE 流
with entry_col:
    st.subheader("📥 Entry Agent")
    entry_placeholder = st.empty()

with review_col:
    st.subheader("🔍 Review Agent")
    review_placeholder = st.empty()

with analysis_col:
    st.subheader("📊 Analysis Agent")
    analysis_placeholder = st.empty()

# 使用 astream_events 过滤各 Agent 的 token 流
async for event in graph.astream_events(user_input, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        agent = event["tags"][0]  # 根据 tag 路由到对应面板
        token = event["data"]["chunk"].content
        route_to_panel(agent, token, placeholders)
```

### 4.6 阶段二：静默执行端

```
飞书对话/群聊 @机器人
        ↓
飞书开放平台事件回调（长连接或公网 URL）
        ↓
轻量 Trigger（转发用户消息到已有 API）
        ↓
已稳定的 LangGraph Orchestrator
        ↓
┌────────────────────┐     ┌────────────────────┐
│ 写入飞书多维表格     │     │ 推送消息到用户       │
└────────────────────┘     └────────────────────┘
```

### 4.7 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| Agent 编排 | LangGraph + LangChain | 核心框架 |
| 链路追踪 | LangSmith | 开发调试必备 |
| 飞书接入 | Feishu SDK (Python) | 多维表格 API |
| 数据存储 | SQLite | 数据流存储 + Checkpointer |
| 控制台 | Streamlit | 开发调试 + Demo 展示 |
| 数据源 | 模拟电商数据 | 订单/销售/库存/用户 |
| 流式输出 | SSE + astream_events v2 | 分轨实时展示 |
| 限流 | 令牌桶 + asyncio | FeishuApiClient 底层 |

---

## 五、开源亮点

| 亮点 | 说明 | 面试价值 |
|------|------|---------|
| **透明化推理** | 每个 Agent 执行过程分轨可见 | 可截图展示架构 |
| **串出并行拓扑** | Entry 串行 + Review/Analysis/Risk 并行 | 可讲拓扑设计原因 |
| **数据/控制流分离** | State 只存引用，数据存 SQLite | 避免 Context 爆炸 |
| **限流封装** | 令牌桶 + 重试 + 429 退避 | 工程完整性 |
| **Checkpointer 中断** | 真正的 Human-in-loop | 高级特性 |
| **分轨看板** | 多 Agent 并行可视化 | Demo 震撼力强 |
| **双入口架构** | 控制台 + Bot，阶段演进清晰 | 可讲架构设计思路 |
| **飞书生态** | 真实用户场景，非 Demo toy | 产品落地能力 |

---

## 六、开发阶段划分

### Phase 1: 核心逻辑（1-2周）
- [ ] LangGraph 项目脚手架搭建（Python 环境、依赖安装）
- [ ] 6 个 Agent 定义与 Tool 定义
- [ ] Graph 拓扑实现（Entry 串行 + 三节点并行）
- [ ] DataStore（SQLite 数据层）
- [ ] 模拟电商数据生成器
- [ ] 基础 Graph 执行（无 Streamlit）

### Phase 2: Human-in-loop + Checkpointer（1周）
- [ ] SqliteSaver Checkpointer 集成
- [ ] interrupt_after 配置
- [ ] Graph 挂起/恢复逻辑
- [ ] 用户确认 UI 卡片

### Phase 3: Streamlit 控制台（1周）
- [ ] 分轨看板布局（st.columns）
- [ ] SSE 分轨展示（astream_events v2）
- [ ] 任务输入 + 结果展示

### Phase 4: 飞书集成（1周）
- [ ] FeishuApiClient（限流 + 重试）
- [ ] 飞书多维表格 API 读写
- [ ] 控制台 + 表格联动

### Phase 5: 开源发布（时间待定）
- [ ] GitHub 仓库创建
- [ ] README + 文档
- [ ] Demo 视频
- [ ] 飞书 Bot 接入（可选，Phase 2 扩展）

---

## 七、竞品分析

| 产品 | 类型 | AI 能力 | 透明化 | 多 Agent | 数据分离 | 开源 |
|------|------|---------|--------|---------|---------|------|
| 飞书智能表格 | 官方功能 | 弱 | 无 | 无 | 无 | 否 |
| Airtable AI | 商业 | 中等 | 无 | 无 | 无 | 否 |
| **TransparentSheet** | 开源 | 强 | 有 | 有 | 有 | 是 |

---

## 八、风险与挑战

| 风险 | 影响 | 应对 |
|------|------|------|
| 飞书 API 429 | 并发写入触发限流 | 令牌桶限流 + 指数退避 |
| Context 爆炸 | 全量数据塞进 State | 数据/控制流分离，只存引用 |
| LLM 幻觉 | 数据分析结果不准确 | 规则引擎兜底 + 人工确认 |
| Checkpointer 挂起 | 状态持久化 + 恢复逻辑复杂 | Phase 2 集中实现 |
| Agent 并行交错 | 多 Agent 日志混在一起 | 分轨看板 + astream_events 过滤 |

---

## 九、备注

- 阶段一专注核心 Agent 协作逻辑，不依赖飞书 Bot 能力
- 所有 Agent 输出使用中文，便于面试展示
- Entry Agent 是下游的前置依赖，必须先完成
- State 只传控制流信息（IDs、状态），数据存 SQLite
- Human-in-loop 通过 Checkpointer 的 interrupt_after 实现
