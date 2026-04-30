# TransparentSheet — 多维表格多智能体虚拟组织

> 飞书多维表格上的多 Agent 虚拟运营团队，让 AI Agent 像真实团队成员一样各司其职、互相协作。

**文档版本：** 1.0
**创建日期：** 2026-04-30
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

### 2.1 标准执行流程

```
用户发指令
    ↓
Orchestra Conductor 理解任务、拆解子任务
    ↓
┌──────────────────────────────────────────────┐
│           4 个 Agent 并行执行                 │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  │
│  │ Entry │  │Review │  │Analysis│  │ Risk  │  │
│  │ Agent │  │ Agent │  │ Agent │  │ Agent │  │
│  └───────┘  └───────┘  └───────┘  └───────┘  │
└──────────────────────────────────────────────┘
    ↓
Report Agent 汇总结果、生成报告
    ↓
用户确认/调整（Human-in-loop）
    ↓
写入飞书多维表格
```

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
| **Entry Agent** | 数据员 | 数据采集、格式转换、模拟数据生成 | 已更新的表格数据 |
| **Review Agent** | 审核 | 完整性检查、规则校验、异常标注 | 审核报告 + 异常列表 |
| **Analysis Agent** | 分析师 | 统计分析、趋势计算、摘要生成 | 数据分析结论 |
| **Risk Agent** | 风控 | 异常检测、风险评级、预警触发 | 风险清单 + 预警 |
| **Report Agent** | 秘书 | 报告生成、周报撰写、建议输出 | 格式化报告 |

### 3.2 Orchestrator 状态机设计

```python
class OrchestrationState(TypedDict):
    task: str                          # 用户任务描述
    intent: str                         # 理解后的意图
    sub_tasks: list[str]               # 拆解后的子任务
    agent_outputs: dict[str, Any]      # 各 Agent 输出
    pending_confirmations: list[dict]  # 待用户确认项
    confirmed_data: dict[str, Any]     # 用户确认后的数据
    status: str                        # pending/running/awaiting_confirm/completed
    error: str | None                   # 错误信息
```

### 3.3 Graph 节点与边

```
Nodes:
- orchestration_node     # 理解任务、拆解子任务
- entry_node            # 数据录入
- review_node           # 数据审核
- analysis_node         # 数据分析
- risk_node             # 风控检测
- report_node           # 报告生成
- human_confirm_node    # 用户确认（阻塞）
- writeback_node        # 写回飞书表格

Edges:
- START → orchestration_node
- orchestration_node → [entry_node, review_node, analysis_node, risk_node]  # 条件路由
- [entry_node, review_node, analysis_node, risk_node] → report_node
- report_node → human_confirm_node
- human_confirm_node → [report_node (调整) / writeback_node (确认)]
- writeback_node → END
```

---

## 四、技术架构

### 4.1 阶段一：控制台模式（当前重点）

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit 控制台                          │
│  ┌─────────┐  ┌────────────────────────┐  ┌──────────────┐  │
│  │ 聊天输入 │  │  Agent 执行过程展示     │  │ 飞书表格预览 │  │
│  │         │  │  (SSE 流式输出)        │  │   iframe    │  │
│  └─────────┘  └────────────────────────┘  └──────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             ↓
                    ┌─────────────────┐
                    │  LangGraph       │
                    │  Orchestrator    │
                    └─────────────────┘
                             ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Entry    │  │ Review   │  │Analysis │  │  Risk   │
│ Agent    │  │ Agent   │  │ Agent   │  │ Agent   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
                             ↓
                    ┌─────────────────┐
                    │ Report Agent    │
                    └─────────────────┘
                             ↓
                    ┌─────────────────┐
                    │  SQLite         │  ← 反馈数据存储
                    │ (反馈闭环)       │
                    └─────────────────┘
```

### 4.2 阶段二：静默执行端（未来扩展）

```
飞书对话/群聊 @机器人
        ↓
飞书开放平台事件回调
        ↓
轻量 Trigger（转发用户消息）
        ↓
已成熟的 LangGraph API
        ↓
┌────────────────────┐     ┌────────────────────┐
│ 写入飞书多维表格    │     │ 推送消息到用户      │
└────────────────────┘     └────────────────────┘
```

### 4.3 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| Agent 编排 | LangGraph + LangChain | 核心框架 |
| 链路追踪 | LangSmith | 开发调试必备 |
| 飞书接入 | Feishu SDK (Python) | 多维表格 API |
| 数据存储 | SQLite | 反馈闭环数据 |
| 控制台 | Streamlit | 开发调试 + Demo 展示 |
| 数据源 | 模拟电商数据 | 订单/销售/库存/用户 |
| 流式输出 | SSE (Server-Sent Events) | 实时展示 Agent 执行 |

---

## 五、开源亮点

| 亮点 | 说明 | 面试价值 |
|------|------|---------|
| **透明化推理** | 每个 Agent 执行过程逐步可见 | 可截图展示架构 |
| **流式输出** | SSE 实时打字机效果展示 Agent "汇报" | Demo 演示震撼 |
| **双入口架构** | 聊天 + 表格按钮，阶段演进清晰 | 可讲架构设计思路 |
| **反馈闭环** | 用户确认数据存储用于 Agent 改进 | 体现工程完整性 |
| **飞书生态** | 真实用户场景，非 Demo toy | 产品落地能力 |

---

## 六、开发阶段划分

### Phase 1: 核心逻辑（1-2周）
- [ ] LangGraph 项目脚手架搭建
- [ ] 6 个 Agent 定义与实现
- [ ] 模拟数据生成
- [ ] 基础 Streamlit 控制台

### Phase 2: 飞书集成（1周）
- [ ] 飞书多维表格 API 接入
- [ ] 数据读写能力
- [ ] 控制台 + 表格联动

### Phase 3: 流式输出（3-5天）
- [ ] SSE 流式展示
- [ ] Agent 执行过程可视化
- [ ] 飞书表格 iframe 预览

### Phase 4: 反馈闭环（3-5天）
- [ ] 用户确认交互
- [ ] SQLite 数据存储
- [ ] 反馈数据应用

### Phase 5: 开源发布（时间待定）
- [ ] GitHub 仓库创建
- [ ] README + 文档
- [ ] Demo 视频

---

## 七、竞品分析

| 产品 | 类型 | AI 能力 | 透明化 | 多 Agent | 开源 |
|------|------|---------|--------|---------|------|
| 飞书智能表格 | 官方功能 | 弱 | 无 | 无 | 否 |
| Airtable AI | 商业 | 中等 | 无 | 无 | 否 |
| **TransparentSheet** | 开源 | 强 | 有 | 有 | 是 |

---

## 八、风险与挑战

| 风险 | 影响 | 应对 |
|------|------|------|
| 飞书 API 限制 | 多维表格字段类型限制 | 分阶段接入，先做支持的功能 |
| LLM 幻觉 | 数据分析结果不准确 | 规则引擎兜底 + 人工确认 |
| 流式输出延迟 | SSE 卡顿影响体验 | 分段输出 + 加载提示 |

---

## 九、备注

- 阶段一专注核心 Agent 协作逻辑，不依赖飞书 Bot 能力
- 所有 Agent 输出使用中文，便于面试展示
- 反馈数据存储用于后续微调或 RAG 改进
