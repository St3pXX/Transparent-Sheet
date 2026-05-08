# Agent 职责矩阵

## Agent 一览

| Agent | 角色 | 核心能力 | 输出 |
|-------|------|---------|------|
| **Orchestra Conductor** | 调度 | 意图理解、任务拆解、路由分发 | intent + sub_tasks |
| **Entry Agent** | 数据员 | 数据采集、用户补充信息收集 | record_ids |
| **Review Agent** | 审核 | 完整性检查、规则校验、异常标注 | anomaly_record_ids |
| **Analysis Agent** | 分析师 | 统计分析、趋势计算、摘要生成 | analysis_summary |
| **Risk Agent** | 风控 | 异常检测、风险评级、预警触发 | risk_levels |
| **Report Agent** | 秘书 | 报告生成、周报撰写、建议输出 | report_content + pending_confirmations |

## 执行拓扑

```
Orchestra Conductor（总调度）
       │
       ├─→ Entry Agent（前置依赖，串行）
       │         │
       │         └─→ [review_node, analysis_node, risk_node]（并行，共享 record_ids）
       │                      │
       │                      └─→ Report Agent
       │                                │
       │                                └─→ writeback_node（飞书表格）
       │
       └─→（直接→ 并行节点，当数据已存在时跳过 Entry）
```

## 状态字段映射

```python
class OrchestrationState(TypedDict):
    # 数据引用
    record_ids: list[str]           # Entry Agent 写入的记录 ID 列表
    anomaly_record_ids: list[str]   # Review Agent 标记的异常 ID（anomaly ⊆ record_ids）

    # Agent 执行结果
    agent_status: dict[str, str]   # agent_name → success / failed / skipped
    agent_outputs: dict[str, str]  # agent_name → 输出摘要

    # 分析与报告
    risk_levels: dict[str, str]     # record_id → high / medium / low
    analysis_summary: str           # Analysis Agent 结论
    report_content: str             # Report Agent 生成的报告
    original_report: str            # 原始报告（用于对比用户修改）
    pending_confirmations: list[dict]  # 待用户确认项

    # 流程控制
    confirmed: bool                 # 用户是否已确认
    confirmed_modifications: list[dict]  # 用户修改记录
    status: str                     # pending / running / awaiting_confirm / completed / error
```

## 部分失败处理

当某个并行 Agent 失败时：

1. 标记 `agent_status[agent_name] = "failed"`
2. Report Agent 仍生成报告，但注明"XX 分析因异常未完成"
3. 流程继续，不阻塞整个 Graph

```python
def handle_partial_failure(state: OrchestrationState) -> OrchestrationState:
    failed_agents = [name for name, status in state["agent_status"].items()
                     if status == "failed"]
    if failed_agents:
        state["report_content"] += f"\n\n⚠️ 以下分析未能完成：{', '.join(failed_agents)}"
    return state
```
