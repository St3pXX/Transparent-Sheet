# ADR-001: 采用 LangGraph 作为 Agent 编排框架

**日期**：2026-04-30
**状态**：已接受

## 背景

需要为 TransparentSheet 选择一个 Agent 编排框架，支持复杂的节点拓扑（串行 + 并行 + fan-in）、中断恢复、流式输出。

## 决策

采用 **LangGraph + LangChain** 作为核心编排框架。

## 理由

| 考量 | LangGraph | LangChain native | CrewAI |
|------|-----------|-----------------|--------|
| 中断/恢复 | 内置 Checkpointer + interrupt_before | 无 | 无 |
| 复杂拓扑 | StateGraph + conditional edges | 有限 | 一般 |
| 流式输出 | astream_events v2 | astream | 支持 |
| 与 LangChain 生态兼容 | 原生 | 原生 | 需要适配 |
| Checkpointer 持久化 | SQLite/Postgres/内存 | 无 | 无 |

LangGraph 的 `interrupt_before` + `SqliteSaver` 组合完美满足 Human-in-loop 需求。

## 后果

- **正面**：开箱即用的中断恢复、成熟生态
- **负面**：学习曲线，LangGraph 复杂度较高
