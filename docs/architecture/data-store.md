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

| 实现类 | 后端 | 依赖 | 适用场景 |
|--------|------|------|---------|
| `SQLiteDataStore` | aiosqlite | 内置 | 单机开发（默认） |
| `PostgresDataStore` | asyncpg | `pip install -e '.[postgres]'` | 生产部署 |
| `TursoDataStore` | libsql-experimental | `pip install -e '.[turso]'` | 边缘部署 |

### 工厂切换

通过 `DATASTORE_BACKEND` 环境变量选择后端：

```bash
export DATASTORE_BACKEND=sqlite    # 默认
export DATASTORE_BACKEND=postgres  # PostgreSQL
export DATASTORE_BACKEND=turso     # Turso/libSQL
```

工厂函数 `create_datastore()` 在 `datastore/factory.py` 中，根据环境变量返回对应实例。

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
