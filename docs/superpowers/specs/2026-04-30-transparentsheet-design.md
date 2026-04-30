# TransparentSheet — 多维表格多智能体虚拟组织

> 飞书多维表格上的多 Agent 虚拟运营团队，让 AI Agent 像真实团队成员一样各司其职、互相协作。

**文档版本：** 2.0
**创建日期：** 2026-04-30
**更新日期：** 2026-04-30
**状态：** 设计阶段（审核完成）

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

### 1.4 生产环境声明

> ⚠️ **重要**：Phase 1-4 使用 SQLite 作为数据存储，仅适用于单机单用户 Demo。开源前必须提供可替换后端（如 PostgreSQL、Turso）的抽象接口。

---

## 二、业务流程

### 2.1 标准执行流程

```
用户发指令
    ↓
Orchestra Conductor 理解任务、拆解子任务
    ↓
[用户确认任务计划] (可选，早期 Human-in-loop)
    ↓
Entry Agent 补录/清洗数据（前置依赖，必须先完成）
    ↓
┌─────────────────────────────────────────────┐
│        3 个 Agent 并行执行（串出并行）          │
│                                                │
│   review_node    analysis_node    risk_node   │
│   (各从 DataStore 读取 record_ids，           │
│    无相互调用关系，共享数据源)                 │
└─────────────────────────────────────────────┘
    ↓
Report Agent 汇总结果、生成报告
    ↓
finish_report_node (空节点，仅用作中断点)
    ↓
Graph 挂起（interrupt_before="writeback_node"）
    ↓
用户确认/调整（通过 ConfirmationChannel）
    ↓
writeback_node (写入飞书表格)
    ↓
END
```

> ⚠️ **关键设计说明**：
> - Entry 是所有下游的前置依赖，必须串行先完成
> - Review / Analysis / Risk 三个节点**共享数据源**，无相互调用关系
> - 中断点设在 `finish_report_node`（report 完成后、writeback 前），而非 report_node 内部

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
| **Orchestra Conductor** | 调度 | 意图理解、任务拆解、路由分发 | 任务执行计划（intent + sub_tasks） |
| **Entry Agent** | 数据员 | 数据采集、用户补充信息收集 | record_ids（写入的记录 ID 列表） |
| **Review Agent** | 审核 | 完整性检查、规则校验、异常标注 | anomaly_record_ids |
| **Analysis Agent** | 分析师 | 统计分析、趋势计算、摘要生成 | analysis_summary（含指标 + 数据来源） |
| **Risk Agent** | 风控 | 异常检测、风险评级、预警触发 | risk_levels |
| **Report Agent** | 秘书 | 报告生成、周报撰写、建议输出 | report_content + pending_confirmations |

> ⚠️ **重要**：Demo 数据生成器从 Entry Agent 剥离，作为独立的 `DemoDataProvider` 工具，仅在控制台模式下注入，不混入业务逻辑。

### 3.2 Agent 状态管理

```python
class OrchestrationState(TypedDict):
    task_id: str                         # 任务唯一 ID（UUID）
    user_id: str                         # 用户 ID（用于 Checkpointer 隔离）
    task: str                            # 用户原始任务描述
    intent: str                          # 理解后的意图
    sub_tasks: list[str]                 # 拆解后的子任务列表

    # 数据引用（控制流）
    record_ids: list[str]                # 全量记录 ID（只增不减）
    anomaly_record_ids: list[str]        # 异常记录 ID（anomaly_record_ids ⊆ record_ids）

    # Agent 执行结果
    agent_status: dict[str, str]         # agent_name → status (success/failed/skipped)
    agent_outputs: dict[str, str]         # agent_name → output_summary（摘要，非全量）

    # 分析与报告
    risk_levels: dict[str, str]          # record_id → risk_level (high/medium/low)
    analysis_summary: str                # 分析结论（含数据来源和置信度）
    report_content: str                  # 报告内容
    original_report: str                 # 原始报告（用于对比修改）
    pending_confirmations: list[dict]  # 待用户确认项

    # 流程控制
    confirmed: bool                     # 用户是否已确认
    confirmed_modifications: list[dict] # 用户修改记录
    status: Literal["pending", "running", "awaiting_confirm", "completed", "error", "cancelled"]
    error: str | None                   # 错误信息
```

### 3.3 部分失败处理策略

```python
def handle_partial_failure(state: OrchestrationState) -> OrchestrationState:
    """
    如果某个并行 Agent 失败：
    1. 标记该 Agent 状态为 failed
    2. Report Agent 仍生成报告，但注明"XX 分析因异常未完成"
    3. 流程继续，不阻塞整个 Graph
    """
    failed_agents = [name for name, status in state["agent_status"].items()
                     if status == "failed"]
    if failed_agents:
        state["report_content"] += f"\n\n⚠️ 以下分析未能完成：{', '.join(failed_agents)}"
    return state
```

### 3.4 Graph 节点与边

```
START
  ↓
orchestration_node (理解任务、拆解、路由)
  ↓
[human_confirm_plan_node] (可选，早期 HITL)
  ↓
entry_node (仅当需要数据录入时)
  ↓
┌─────────────────────────────────────────┐
│        并行执行（共享 record_ids）          │
│   review_node    analysis_node    risk_node │
│   (各从 DataStore 查询，无相互调用)        │
└─────────────────────────────────────────┘
  ↓
report_node (生成报告 + 待确认项)
  ↓
finish_report_node (空节点，中断点)
  ↓
(interrupt_before="writeback_node")
  ↓
┌─────────────────────────────────────────┐
│    ConfirmationChannel (外部处理)         │
│    - StreamlitChannel (Phase 1-4)        │
│    - FeishuCardChannel (Phase 5)        │
└─────────────────────────────────────────┘
  ↓
[用户调整 → revise_report_node]
    或
[用户确认 → writeback_node]
  ↓
writeback_node (写入飞书表格)
  ↓
END

条件边逻辑：
- orchestration_node → entry_node (当需要数据录入时)
- orchestration_node → [review_node, analysis_node, risk_node] (当数据已存在时)
- entry_node → [review_node, analysis_node, risk_node] (固定串出并行)
- review_node + analysis_node + risk_node → report_node (fan_in，汇合后执行)
- report_node → finish_report_node (无条件)
- finish_report_node → [writeback_node] (用户确认时)
- finish_report_node → [revise_report_node] (用户调整时)
```

---

## 四、技术架构

### 4.1 数据与控制流分离原则

```
┌──────────────────────────────────────────────────────────┐
│  LangGraph State（控制流）                                  │
│  只存：task_id, user_id, record_ids, status, 摘要         │
│  大小：< 1KB / 任务                                        │
└──────────────────────────────────────────────────────────┘
                         ↕ (通过 record_id 关联)
┌──────────────────────────────────────────────────────────┐
│  DataStore（数据流，抽象接口）                               │
│  ┌────────────────────────────────────────────────┐    │
│  │ interface AbstractDataStore                      │    │
│  │   async def save_records(...)                   │    │
│  │   async def get_records(...)                    │    │
│  │   async def save_agent_output(...)              │    │
│  │   async def get_agent_output(...)               │    │
│  │   async def save_confirmation(...)              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  实现：                                                  │
│  - SQLiteDataStore (Phase 1-4, aiosqlite)               │
│  - PostgresDataStore (开源前可选)                         │
│  - TursoDataStore (开源前可选)                           │
└──────────────────────────────────────────────────────────┘
```

> ⚠️ **重要**：使用 `aiosqlite` 替代同步 `sqlite3`，确保与 asyncio 兼容。DataStore 定义抽象基类，后续切换零成本。

### 4.2 阶段一：控制台模式

```
┌──────────────────────────────────────────────────────────────────┐
│                     Streamlit 控制台（看板布局）                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐     │
│  │  任务输入 │  Entry   │  Review  │ Analysis │ Risk+Report │     │
│  │  (左侧)  │  面板    │  面板    │  面板    │   面板      │     │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                     LangGraph Orchestrator
                     (配置 interrupt_before="writeback_node")
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                      DataStore（异步抽象层）                       │
│  - aiosqlite 实现                                                 │
│  - 表格全量内容                                                    │
│  - 各 Agent 中间输出                                               │
│  - 用户确认记录                                                    │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌────────────────────────┐
                    │   FeishuApiClient      │
                    │   (统一限流 + 重试)    │
                    └────────────────────────┘
                              ↓
                    飞书多维表格（展示层）
```

### 4.3 FeishuApiClient 设计

```python
class FeishuApiClient:
    """
    统一的飞书 API 客户端
    - 令牌桶限流（全局单一令牌桶，所有接口共享 QPS）
    - token 自动刷新（带互斥锁防止重复刷新）
    - Retry-After 头优先 + 指数退避兜底
    """

    def __init__(self, app_id: str, app_secret: str, qps: int = 20):
        self._rate_limiter = TokenBucketRateLimiter(qps=qps)
        self._semaphore = asyncio.Semaphore(10)
        self._tenant_token: str | None = None
        self._token_expires_at: float = 0
        self._token_lock = asyncio.Lock()

    async def _get_tenant_token(self) -> str:
        """带锁的 token 自动刷新"""
        async with self._token_lock:
            if time.time() >= self._token_expires_at:
                self._tenant_token = await self._fetch_token()
                self._token_expires_at = time.time() + 7200  # 2小时
            return self._tenant_token

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        """统一请求封装：限流 + token + 重试"""
        await self._rate_limiter.acquire()
        await self._semaphore.acquire()

        for attempt in range(3):
            try:
                response = await self._do_request(method, url, **kwargs)
                return response
            except Feishu429Error as e:
                # 优先使用 Retry-After 头
                retry_after = e.retry_after or (2 ** attempt)
                await asyncio.sleep(retry_after)
                continue

        raise FeishuAPIError("Max retries exceeded")

    async def batch_create_records(self, table_id: str, records: list[dict]):
        """分批写入，避免 429"""
        BATCH_SIZE = 10
        created_ids = []
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            result = await self._request("POST", f"/bitable/v1/apps/{table_id}/tables/records/batch_create", json={"records": batch})
            created_ids.extend([r["record_id"] for r in result["data"]["records"]])
        return created_ids
```

> 限流参数：QPS=20（保守值），最大并发=10，写入批次=10，Retry-After 优先 + 最大重试 3 次。

### 4.4 Human-in-loop：中断与恢复

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 持久化 Checkpointer（禁用 :memory:）
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# 编译 Graph
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["writeback_node"]  # writeback 前中断
)

# 执行流程
# Step 1: 运行到 finish_report_node，Graph 自动挂起
config = {
    "configurable": {
        "thread_id": f"{user_id}:{task_id}",  # 用户隔离
        "user_id": user_id
    }
}
for event in graph.stream(user_input, config, stream_mode="values"):
    if event.get("status") == "awaiting_confirm":
        break  # Graph 已挂起

# Step 2: ConfirmationChannel 处理用户确认
channel = ConfirmationChannelFactory.create("streamlit")
await channel.render_confirmation(event)
user_response = await channel.wait_for_response()

# Step 3: 根据响应恢复执行
if user_response.action == "confirm":
    graph.update_state(config, {
        "confirmed": True,
        "confirmed_modifications": user_response.modifications
    })
    for event in graph.stream(None, config):
        ...  # writeback_node
elif user_response.action == "revise":
    graph.update_state(config, {
        "confirmed_modifications": user_response.modifications
    })
    for event in graph.stream({"type": "revise"}, config):
        ...  # revise_report_node → writeback_node
```

### 4.5 ConfirmationChannel 接口抽象

```python
from abc import ABC, abstractmethod

class ConfirmationChannel(ABC):
    """确认渠道抽象，用于解耦 Streamlit 和飞书 Bot 的交互"""

    @abstractmethod
    async def render_confirmation(self, state: OrchestrationState): ...

    @abstractmethod
    async def wait_for_response(self) -> ConfirmationResponse: ...

class StreamlitChannel(ConfirmationChannel):
    """Phase 1-4：Streamlit 实现"""
    ...

class FeishuCardChannel(ConfirmationChannel):
    """Phase 5：飞书消息卡片实现"""
    ...

class ConfirmationChannelFactory:
    @staticmethod
    def create(channel_type: str) -> ConfirmationChannel:
        channels = {
            "streamlit": StreamlitChannel,
            "feishu": FeishuCardChannel,
        }
        return channels[channel_type]()
```

### 4.6 Streamlit 分轨展示

```python
# 3 列分轨布局
left_col, entry_col, review_col, analysis_col = st.columns([1, 1, 1, 1])
bottom_row = st.columns([1, 1])

# 使用 node_name 而非 tags[0] 路由
async for event in graph.astream_events(user_input, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        node_name = event.get("name")  # 节点名在 metadata 中
        token = event["data"]["chunk"].content

        # 路由到对应面板
        if node_name == "entry_node":
            entry_placeholder.write(token)
        elif node_name == "review_node":
            review_placeholder.write(token)
        elif node_name == "analysis_node":
            analysis_placeholder.write(token)
        elif node_name in ["report_node", "finish_report_node"]:
            bottom_row[0].write(token)
```

> ⚠️ 使用 `event.get("name")` 获取节点名，比 `event["tags"][0]` 更可靠。

### 4.7 错误处理架构

```python
def error_handler_node(state: OrchestrationState, error: Exception) -> OrchestrationState:
    """全局错误处理器"""
    state["status"] = "error"
    state["error"] = str(error)

    # 最多重试一次
    if not state.get("_retried"):
        state["_retried"] = True
        return Command(goto="重试失败的节点")
    else:
        return state

# Graph 编译时注入错误处理
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["writeback_node"],
    on_vertex_error=error_handler_node
)
```

### 4.8 阶段二：静默执行端

```
飞书对话/群聊 @机器人
        ↓
飞书开放平台事件回调
        ↓
轻量 Trigger（转发用户消息）
        ↓
已稳定的 LangGraph Orchestrator
        ↓
ConfirmationChannelFactory.create("feishu") → 飞书消息卡片确认
        ↓
┌────────────────────┐     ┌────────────────────┐
│ 写入飞书多维表格     │     │ 推送消息到用户       │
└────────────────────┘     └────────────────────┘
```

### 4.9 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| Agent 编排 | LangGraph + LangChain | 核心框架 |
| 链路追踪 | LangSmith | 开发调试必备 |
| 飞书接入 | Feishu SDK (Python) | 多维表格 API |
| 数据存储 | aiosqlite（异步） | 数据流存储 + Checkpointer |
| 存储抽象 | 抽象基类设计 | PostgreSQL / Turso 可替换 |
| 控制台 | Streamlit | 开发调试 + Demo 展示 |
| 数据源 | DemoDataProvider | 独立工具，不混入 Agent 逻辑 |
| 流式输出 | SSE + astream_events v2 | 分轨实时展示 |
| 限流 | 令牌桶 + asyncio | FeishuApiClient 底层 |

---

## 五、开源亮点

| 亮点 | 说明 |
|------|------|
| **透明化推理** | 每个 Agent 执行过程分轨可见 |
| **串出并行拓扑** | Entry 串行 + Review/Analysis/Risk 并行，拓扑可解释 |
| **数据/控制流分离** | State 只存引用，数据存 DataStore |
| **异步数据层** | aiosqlite + 抽象基类，后续可替换 |
| **统一限流** | 全局令牌桶 + Retry-After + token 自动刷新 |
| **部分失败容错** | Agent 独立状态标记，失败不阻塞全流程 |
| **中断与恢复** | Checkpointer 持久化 + 用户隔离 |
| **双入口架构** | ConfirmationChannel 抽象，Streamlit/Bot 可替换 |
| **分轨看板** | 多 Agent 并行可视化，视觉震撼 |
| **飞书生态** | 真实用户场景，非 Demo toy |

---

## 六、开发阶段划分

### Phase 1: 核心逻辑（1-2周）
- [ ] LangGraph 项目脚手架搭建（Python 环境、依赖安装）
- [ ] DataStore 抽象层 + aiosqlite 实现
- [ ] DemoDataProvider（独立工具，不混入 Agent）
- [ ] 6 个 Agent 定义与 Tool 定义
- [ ] Graph 拓扑实现（Entry 串行 + 三节点并行 fan_in）
- [ ] 部分失败处理（agent_status 标记）
- [ ] 错误处理器（error_handler_node）
- [ ] 基础 Graph 执行（无 Streamlit）

### Phase 2: Human-in-loop + 中断（1周）
- [ ] SqliteSaver Checkpointer 持久化（禁用 :memory:）
- [ ] interrupt_before 配置
- [ ] finish_report_node + revise_report_node
- [ ] ConfirmationChannel 抽象 + StreamlitChannel 实现
- [ ] Graph 挂起/恢复逻辑
- [ ] 用户确认 UI 卡片

### Phase 3: Streamlit 控制台（1周）
- [ ] 分轨看板布局（st.columns）
- [ ] SSE 分轨展示（astream_events v2，node_name 路由）
- [ ] 任务输入 + 结果展示
- [ ] 早期 Human-in-loop（任务计划确认）

### Phase 4: 飞书集成（1周）
- [ ] FeishuApiClient（统一限流 + token 刷新 + Retry-After）
- [ ] 飞书多维表格 API 读写
- [ ] 控制台 + 表格联动
- [ ] FeishuCardChannel（Phase 5 扩展预留）

### Phase 5: 开源发布（时间待定）
- [ ] DataStore 抽象层完善（PostgreSQL / Turso 可替换）
- [ ] GitHub 仓库创建
- [ ] README + 文档
- [ ] Demo 视频
- [ ] 飞书 Bot 接入

---

## 七、竞品分析

| 产品 | 类型 | AI 能力 | 透明化 | 多 Agent | 数据分离 | 异步安全 | 开源 |
|------|------|---------|--------|---------|---------|---------|------|
| 飞书智能表格 | 官方功能 | 弱 | 无 | 无 | 无 | 无 | 否 |
| Airtable AI | 商业 | 中等 | 无 | 无 | 无 | 无 | 否 |
| **TransparentSheet** | 开源 | 强 | 有 | 有 | 有 | 有 | 是 |

---

## 八、风险与挑战

| 风险 | 影响 | 应对 |
|------|------|------|
| 飞书 API 429 | 并发写入触发限流 | 全局令牌桶 + Retry-After + 指数退避 |
| Context 爆炸 | 全量数据塞进 State | 数据/控制流分离，只存引用 |
| LLM 幻觉 | 数据分析结果不准确 | 规则引擎兜底 + 人工确认 + 建议标注数据来源 |
| Checkpointer 挂起 | 状态持久化 + 恢复逻辑复杂 | Phase 2 集中实现 |
| Agent 并行交错 | 多 Agent 日志混在一起 | 分轨看板 + node_name 路由 |
| SQLite 并发 | 文件数据库跨线程访问 | aiosqlite + WAL 模式 |
| 部分失败 | 单 Agent 失败导致全流程中断 | agent_status 标记 + 降级处理 |
| token 过期 | API 调用失败 | 带锁自动刷新 |
| 多用户状态混淆 | Checkpointer 数据混乱 | thread_id + user_id 双重隔离 |

---

## 九、测试方案

| 测试类型 | 工具 | 说明 |
|---------|------|------|
| 单元测试 | pytest | Agent 逻辑、Tool、DataStore |
| API Mock | vcrpy / respx | FeishuApiClient 录制/回放 |
| 集成测试 | FakeLLM | LangGraph Agent 链路测试 |
| E2E 录制 | playwright | Demo 自动化录制 GIF |

---

## 十、备注

- 阶段一专注核心 Agent 协作逻辑，不依赖飞书 Bot 能力
- 所有 Agent 输出使用中文，便于面试展示
- Entry Agent 是下游的前置依赖，必须先完成
- State 只传控制流信息（IDs、状态），数据存 DataStore
- Demo 数据生成器独立，不混入 Agent 业务逻辑
- DataStore 定义抽象基类，后续可零成本替换后端
- Checkpointer 必须持久化（禁用 :memory:）
- ConfirmationChannel 抽象，Streamlit/Bot 可替换
- SQLite 仅适用于 Phase 1-4 单机 Demo，开源前提供可替换后端
