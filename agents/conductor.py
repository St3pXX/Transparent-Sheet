from langgraph.prebuilt import create_react_agent  # noqa: F401
from transparent_sheet.llm import get_llm
from transparent_sheet.orchestration.state import OrchestrationState

SYSTEM_PROMPT = """你是一个电商运营虚拟团队的 Orchestra Conductor（调度员）。
你的职责：
1. 理解用户任务，判断意图（intent）
2. 拆解为子任务列表（sub_tasks）
3. 判断是否需要 Entry Agent（数据是否需要录入）
4. 路由到对应 Agent

意图分类：
- 数据补录/清洗 → 需要 Entry Agent
- 数据完整性检查 → Review Agent
- 销售分析/趋势 → Analysis Agent
- 风险预警/库存异常 → Risk Agent
- 周报生成 → Report Agent

你是协调者，不执行具体分析，只做规划和路由。"""

def build_conductor_agent():
    llm = get_llm(temperature=0.3)
    return create_react_agent(llm, tools=[], state_schema=OrchestrationState)