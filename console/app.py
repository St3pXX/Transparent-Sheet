import streamlit as st
import asyncio
import uuid
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.orchestration.graph import build_graph
from transparent_sheet.datastore.sqlite import SQLiteDataStore
from transparent_sheet.channels.streamlit import StreamlitChannel
from transparent_sheet.agents.tools.datastore import set_store


def main():
    st.set_page_config(page_title="TransparentSheet 控制台", layout="wide")
    st.title("TransparentSheet 多智能体运营平台")

    if "task_id" not in st.session_state:
        st.session_state.task_id = str(uuid.uuid4())
        st.session_state.user_id = "demo-user"

    # Initialize DataStore
    if "store" not in st.session_state:
        store = SQLiteDataStore("transparent_sheet.db")
        asyncio.get_event_loop().run_until_complete(store.init_schema())
        st.session_state.store = store
        set_store(store)

    # Task input
    user_input = st.text_area("输入运营任务", placeholder="例如：补全本周销售数据并生成本周运营周报")

    if st.button("🚀 执行"):
        # 异步执行 pipeline
        result = asyncio.run(run_pipeline_async(user_input, st.session_state.task_id, st.session_state.user_id))
        st.session_state["last_state"] = result


async def run_pipeline_async(user_input: str, task_id: str, user_id: str):
    graph = build_graph()  # 已包含 checkpointer + interrupt_before

    config = {
        "configurable": {
            "thread_id": f"{user_id}:{task_id}",
            "user_id": user_id,
        }
    }

    # Build initial state
    initial_state: OrchestrationState = {
        "task_id": task_id,
        "user_id": user_id,
        "task": user_input,
        "intent": "",
        "sub_tasks": [],
        "record_ids": [],
        "anomaly_record_ids": [],
        "agent_status": {},
        "agent_outputs": {},
        "risk_levels": {},
        "analysis_summary": "",
        "report_content": "",
        "original_report": "",
        "pending_confirmations": [],
        "confirmed": False,
        "confirmed_modifications": [],
        "status": "pending",
        "error": None,
    }

    # 3 列分轨看板
    left_col, entry_col, review_col, analysis_col = st.columns([1, 1, 1, 1])
    panels = {
        "entry_node": entry_col,
        "review_node": review_col,
        "analysis_node": analysis_col,
    }

    # ⚠️ 必须用 astream() 异步迭代，否则事件循环冲突
    async for event in graph.astream(
        {"messages": [("user", user_input)]},
        config,
        stream_mode="values",
    ):
        if event.get("status") == "awaiting_confirm":
            break

        # TODO: 通过 astream_events v2 获取 node_name 路由到面板
        # current_state = event

    # Confirmation
    channel = StreamlitChannel()
    # st.session_state 中获取最后的 state
    last_state = st.session_state.get("last_state", {})
    await channel.render_confirmation(last_state)
    response = await channel.wait_for_response()

    if response.action == "confirm":
        async for _ in graph.astream(None, config):
            pass  # 继续执行 writeback_node
    elif response.action == "revise":
        async for _ in graph.astream({"type": "revise"}, config):
            pass  # revise_report_node → writeback_node

    return last_state


if __name__ == "__main__":
    main()
