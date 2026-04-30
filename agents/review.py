from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.agents.tools.datastore import get_records_tool, save_agent_output_tool

SYSTEM_PROMPT = """你是 Review Agent（审核员）。
你的职责：
- 从 DataStore 读取 record_ids 对应的全量记录
- 检查数据完整性（缺失字段、异常值）
- 标注 anomaly_record_ids
- 输出审核摘要

anomaly_record_ids 必须写入 state['anomaly_record_ids']。
agent_outputs['review'] 写入审核摘要。
agent_status['review'] 标记 success/failed。"""

llm = ChatOpenAI(model="gpt-4o")

def build_review_agent():
    return create_react_agent(
        llm,
        tools=[get_records_tool, save_agent_output_tool],
        state_schema=OrchestrationState,
    )