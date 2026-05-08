# DataStore 抽象层设计

## 设计原则

- **数据与控制流分离**：LangGraph State 只存引用（record_ids），不存数据本体
- **异步优先**：所有操作均为 async，支持 aiosqlite / asyncio 生态
- **零成本替换**：定义抽象基类，切换后端无需修改业务代码

## 抽象接口

```python
class AbstractDataStore(ABC):
    """DataStore 抽象基类，定义所有数据存储操作"""

    @abstractmethod
    async def init_schema(self) -> None:
        """初始化数据库 schema"""
        ...

    @abstractmethod
    async def save_records(self, task_id: str, records: list[dict]) -> list[str]:
        """保存数据记录，返回 record_ids"""
        ...

    @abstractmethod
    async def get_records(self, task_id: str, record_ids: list[str] | None = None) -> list[dict]:
        """根据 task_id 或 record_ids 获取记录"""
        ...

    @abstractmethod
    async def save_agent_output(
        self, task_id: str, agent_name: str, output: dict
    ) -> None:
        """保存 Agent 中间输出"""
        ...

    @abstractmethod
    async def get_agent_output(self, task_id: str, agent_name: str) -> dict | None:
        """获取指定 Agent 的输出"""
        ...

    @abstractmethod
    async def save_confirmation(
        self, task_id: str, confirmed: bool, modifications: list[dict]
    ) -> None:
        """保存用户确认结果"""
        ...
```

## 实现

| 实现类 | 适用阶段 | 说明 |
|--------|---------|------|
| `SQLiteDataStore` | Phase 1-4 | aiosqlite，单机单用户 Demo |
| `PostgresDataStore` | 开源后 | 可选生产级后端 |
| `TursoDataStore` | 开源后 | 可选边缘部署后端 |

## SQLite 实现要点

- 使用 `aiosqlite` 而非同步 `sqlite3`，确保与 asyncio 兼容
- WAL 模式，提升并发读写性能
- Checkpointer 复用同一数据库文件

## 线程隔离

通过 `task_id` + `user_id` 双重隔离：

```python
config = {
    "configurable": {
        "thread_id": f"{user_id}:{task_id}",
        "user_id": user_id,
    }
}
```
