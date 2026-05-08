# Human-in-loop 确认流程

## 中断点设计

Graph 在 `finish_report_node` 后、`writeback_node` 前中断：

```python
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["writeback_node"]  # writeback 前中断
)
```

## 完整流程

```
1. graph.stream(user_input, config)
   → 执行到 finish_report_node 自动挂起
   → status == "awaiting_confirm"

2. ConfirmationChannel.render_confirmation(state)
   → 展示报告 + 待确认项

3. ConfirmationChannel.wait_for_response()
   → 用户选择 "确认" 或 "修改"

4.1. 确认：
     graph.update_state(config, {"confirmed": True})
     graph.stream(None, config)  → writeback_node

4.2. 修改：
     graph.update_state(config, {"confirmed_modifications": [...]})
     graph.stream({"type": "revise"}, config)  → revise_report_node → writeback_node
```

## ConfirmationChannel 抽象

```python
class ConfirmationChannel(ABC):
    @abstractmethod
    async def render_confirmation(self, state: OrchestrationState): ...

    @abstractmethod
    async def wait_for_response(self) -> ConfirmationResponse: ...

class StreamlitChannel(ConfirmationChannel):
    """Phase 1-4：Streamlit 实现"""

class FeishuCardChannel(ConfirmationChannel):
    """Phase 5：飞书消息卡片实现"""

class ConfirmationChannelFactory:
    @staticmethod
    def create(channel_type: str) -> ConfirmationChannel:
        return {"streamlit": StreamlitChannel, "feishu": FeishuCardChannel}[channel_type]()
```

## 响应类型

```python
@dataclass
class ConfirmationResponse:
    action: Literal["confirm", "revise"]
    modifications: list[dict]  # 用户修改内容
```
