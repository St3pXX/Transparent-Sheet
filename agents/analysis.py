from langgraph.prebuilt import create_react_agent  # noqa: F401
from transparent_sheet.llm import get_llm
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.agents.tools.datastore import get_records_tool, save_agent_output_tool

SYSTEM_PROMPT = """你是 Analysis Agent（分析师）。
你的职责：
- 从 DataStore 读取 record_ids 对应的全量记录
- 做统计分析：销量趋势、地区分布、商品排名
- 生成分析摘要（analysis_summary）
- 分析结果写入 state['analysis_summary']
- agent_outputs['analysis'] 写入输出摘要
- agent_status['analysis'] 标记 success/failed"""

def build_analysis_agent():
    llm = get_llm(temperature=0.3)
    return create_react_agent(
        llm,
        tools=[get_records_tool, save_agent_output_tool],
        state_schema=OrchestrationState,
    )