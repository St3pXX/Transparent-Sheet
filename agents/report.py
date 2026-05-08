from langgraph.prebuilt import create_react_agent  # noqa: F401
from transparent_sheet.config.llm import get_llm
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.agents.tools.datastore import save_agent_output_tool

SYSTEM_PROMPT = """你是 Report Agent（秘书）。
你的职责：
- 综合 Review / Analysis / Risk 三个 Agent 的输出
- 生成完整运营周报
- 标注待用户确认项（pending_confirmations）
- 原始报告写入 state['original_report']
- report_content 写入完整报告
- pending_confirmations 写入待确认项列表
- agent_outputs['report'] 写入输出摘要
- agent_status['report'] 标记 success/failed"""

def build_report_agent():
    llm = get_llm(temperature=0.5)
    return create_react_agent(
        llm,
        tools=[save_agent_output_tool],
        state_schema=OrchestrationState,
    )