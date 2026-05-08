from langgraph.prebuilt import create_react_agent  # noqa: F401
from transparent_sheet.config.llm import get_llm
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.agents.tools.datastore import get_records_tool, save_agent_output_tool

SYSTEM_PROMPT = """你是 Risk Agent（风控员）。
你的职责：
- 从 DataStore 读取 record_ids 对应的全量记录
- 异常检测：低库存、异常高/低价、违约风险
- 风险评级：high / medium / low
- 输出 risk_levels dict: {record_id -> risk_level}
- risk_levels 必须写入 state['risk_levels']
- agent_outputs['risk'] 写入风控摘要
- agent_status['risk'] 标记 success/failed"""

def build_risk_agent():
    llm = get_llm(temperature=0.3)
    return create_react_agent(
        llm,
        tools=[get_records_tool, save_agent_output_tool],
        state_schema=OrchestrationState,
    )