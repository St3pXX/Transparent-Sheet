from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.agents.tools.datastore import save_records_tool

SYSTEM_PROMPT = """你是 Entry Agent（数据员）。
你的职责：采集、录入、清洗数据。
- 如果用户提供数据，使用用户提供的数据
- 如果用户只给指令（如"补全本周销售数据"），使用 demo_data_provider 工具生成模拟数据
- 将记录保存到 DataStore，返回 record_ids

关键：record_ids 必须写入 state['record_ids']，这是所有下游 Agent 的数据入口。
agent_status['entry'] 标记 success/failed。"""

def build_entry_agent():
    llm = ChatOpenAI(model="gpt-4o")
    return create_react_agent(
        llm,
        tools=[save_records_tool],
        state_schema=OrchestrationState,
    )