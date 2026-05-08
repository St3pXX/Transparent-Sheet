# ADR-002: 使用 aiosqlite 而非同步 sqlite3

**日期**：2026-04-30
**状态**：已接受

## 背景

TransparentSheet 大量使用 async/await（StreamlitChannel、FeishuApiClient、LangGraph astream），但 Python 标准库 `sqlite3` 为同步 API。在 async 事件循环中直接调用同步数据库 API 会阻塞事件循环。

## 决策

使用 `aiosqlite` 替代同步 `sqlite3`，DataStore 全部操作均为 async。

## 理由

- 与 asyncio 生态无缝集成，无需 `run_in_executor`
- API 与 sqlite3 相似，迁移成本低
- 足够支撑 Phase 1-4 单机 Demo 性能需求
- 抽象基类设计，开源后可替换为 asyncpg（PostgreSQL）

## 后果

- **正面**：不阻塞事件循环、支持并发读写（WAL 模式）
- **负面**：aiosqlite 维护不活跃（只读更新）、生产环境建议切换到 PostgreSQL
