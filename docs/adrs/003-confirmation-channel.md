# ADR-003: ConfirmationChannel 抽象

**日期**：2026-04-30
**状态**：已接受

## 背景

TransparentSheet 需要支持两种确认交互方式：
1. **Phase 1-4**：Streamlit 控制台内直接确认
2. **Phase 5**：飞书 Bot 消息卡片确认

两种场景的交互协议完全不同，但 Graph 中断/恢复逻辑相同。

## 决策

引入 `ConfirmationChannel` 抽象接口，解耦确认逻辑与具体渠道实现。

## 设计

```python
class ConfirmationChannel(ABC):
    @abstractmethod
    async def render_confirmation(self, state: OrchestrationState): ...

    @abstractmethod
    async def wait_for_response(self) -> ConfirmationResponse: ...

class StreamlitChannel(ConfirmationChannel):
    async def render_confirmation(self, state): ...
    async def wait_for_response(self): ...  # st.rerun() 等待

class FeishuCardChannel(ConfirmationChannel):
    async def render_confirmation(self, state): ...  # 发送飞书卡片
    async def wait_for_response(self): ...  # 回调/WebSocket
```

## 切换方式

```python
channel = ConfirmationChannelFactory.create("streamlit")  # 或 "feishu"
```

## 后果

- **正面**：Phase 1-4 和 Phase 5 完全解耦，Graph 逻辑零修改
- **负面**：需要维护两套确认 UI，增加开发工作量
