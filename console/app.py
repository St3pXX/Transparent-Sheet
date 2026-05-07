import streamlit as st
import asyncio
import uuid
from transparent_sheet.orchestration.state import OrchestrationState
from transparent_sheet.orchestration.graph import build_graph
from transparent_sheet.datastore.sqlite import SQLiteDataStore
from transparent_sheet.channels.streamlit import StreamlitChannel
from transparent_sheet.agents.tools.datastore import set_store

APPLE_CSS = """
<style>
  /* Apple Design System — White Theme */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  :root {
    --apple-bg: #ffffff;
    --apple-surface: #f5f5f7;
    --apple-surface-2: #e8e8ed;
    --apple-text: #1d1d1f;
    --apple-text-secondary: #86868b;
    --apple-blue: #0071e3;
    --apple-blue-hover: #0077ed;
    --apple-green: #34c759;
    --apple-orange: #ff9500;
    --apple-red: #ff3b30;
    --apple-radius: 12px;
    --apple-radius-lg: 20px;
    --apple-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
    --apple-shadow-hover: 0 8px 40px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.04);
    --apple-font: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
  }

  /* Base */
  .stApp {
    background: var(--apple-bg) !important;
    font-family: var(--apple-font) !important;
    color: var(--apple-text) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Main page background */
  [data-testid="stAppViewContainer"] {
    background: var(--apple-bg) !important;
  }

  [data-testid="stHeader"] {
    background: rgba(0,0,0,0) !important;
    border-bottom: none !important;
  }

  [data-testid="stToolbar"] {
    top: 0px !important;
    right: 1rem !important;
  }

  /* Typography */
  h1, h2, h3, h4, h5, h6 {
    font-family: var(--apple-font) !important;
    color: var(--apple-text) !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
  }

  /* Title */
  .app-title {
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--apple-text) !important;
    margin-bottom: 0.2rem;
  }

  /* Cards / white surfaces */
  .stColumn > div,
  [data-testid="stHorizontalBlock"] > div {
    background: var(--apple-bg);
    border-radius: var(--apple-radius-lg);
    box-shadow: var(--apple-shadow);
    padding: 1.5rem;
    border: 1px solid rgba(0,0,0,0.05);
    transition: box-shadow 0.3s ease, transform 0.3s ease;
  }

  [data-testid="stHorizontalBlock"] > div:hover {
    box-shadow: var(--apple-shadow-hover);
    transform: translateY(-2px);
  }

  /* Buttons — Apple Blue */
  .stButton > button {
    background: var(--apple-blue) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 980px !important;
    padding: 0.6rem 2rem !important;
    font-family: var(--apple-font) !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
    box-shadow: 0 2px 8px rgba(0,113,227,0.25), 0 1px 2px rgba(0,0,0,0.08) !important;
    transition: all 0.25s cubic-bezier(0.25, 0.1, 0.25, 1) !important;
    cursor: pointer;
  }

  .stButton > button:hover {
    background: var(--apple-blue-hover) !important;
    box-shadow: 0 4px 16px rgba(0,113,227,0.35), 0 2px 4px rgba(0,0,0,0.10) !important;
    transform: translateY(-1px);
  }

  .stButton > button:active {
    transform: translateY(0px) !important;
    box-shadow: 0 1px 4px rgba(0,113,227,0.20) !important;
  }

  /* Secondary buttons */
  .stButton > button[kind="secondary"] {
    background: var(--apple-surface) !important;
    color: var(--apple-text) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
  }

  /* Text Area */
  .stTextArea > div > div > textarea,
  .stTextInput > div > div > input {
    background: var(--apple-surface) !important;
    border: 1px solid var(--apple-surface-2) !important;
    border-radius: var(--apple-radius) !important;
    color: var(--apple-text) !important;
    font-family: var(--apple-font) !important;
    font-size: 1rem !important;
    padding: 0.8rem 1rem !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.04) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
  }

  .stTextArea > div > div > textarea:focus,
  .stTextInput > div > div > input:focus {
    border-color: var(--apple-blue) !important;
    box-shadow: 0 0 0 3px rgba(0,113,227,0.12), inset 0 1px 3px rgba(0,0,0,0.04) !important;
    outline: none !important;
  }

  /* Labels */
  .stTextArea label,
  .stTextInput label,
  .stMarkdown,
  .stText {
    font-family: var(--apple-font) !important;
    color: var(--apple-text) !important;
  }

  /* Divider */
  [data-testid="stDividerBlock"] {
    border-top: 1px solid var(--apple-surface-2) !important;
    margin: 1.5rem 0 !important;
  }

  /* Subheader */
  .stSubheader {
    font-weight: 600 !important;
    font-size: 1.2rem !important;
    letter-spacing: -0.01em;
    color: var(--apple-text) !important;
  }

  /* Info / Warning / Error boxes */
  .stAlert {
    border-radius: var(--apple-radius) !important;
    border: none !important;
    font-family: var(--apple-font) !important;
  }

  /* Columns gap */
  [data-testid="stHorizontalBlock"] {
    gap: 1.5rem !important;
  }

  /* Smooth scrolling */
  html {
    scroll-behavior: smooth;
  }

  /* Scrollbar — Apple style */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: var(--apple-surface-2);
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: var(--apple-text-secondary);
  }

  /* Page load animation */
  @keyframes appleFadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .stApp {
    animation: appleFadeIn 0.5s cubic-bezier(0.25, 0.1, 0.25, 1) both;
  }

  /* Markdown content styling */
  .stMarkdown p {
    line-height: 1.7;
    color: var(--apple-text);
  }

  /* Status indicators — pill style */
  .status-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.75rem;
    border-radius: 980px;
    font-size: 0.8rem;
    font-weight: 500;
  }
  .status-pill.green { background: rgba(52,199,89,0.12); color: #34c759; }
  .status-pill.orange { background: rgba(255,149,0,0.12); color: #ff9500; }
  .status-pill.red { background: rgba(255,59,48,0.12); color: #ff3b30; }
  .status-pill.blue { background: rgba(0,113,227,0.10); color: #0071e3; }
</style>
"""


def main():
    st.set_page_config(
        page_title="TransparentSheet 控制台",
        page_icon="✨",
        layout="wide",
        menu_items=None,
    )
    st.markdown(APPLE_CSS, unsafe_allow_html=True)
    st.markdown('<p class="app-title">TransparentSheet 多智能体运营平台</p>', unsafe_allow_html=True)

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

    # 4 列分轨看板 — Apple 风格
    left_col, entry_col, review_col, analysis_col = st.columns([1, 1, 1, 1])

    with left_col:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #0071e3 0%, #5856d6 100%);
            border-radius: 20px;
            padding: 2rem 1.5rem;
            color: white;
            text-align: center;
            box-shadow: 0 4px 24px rgba(0,113,227,0.25);
        ">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">🤖</div>
            <div style="font-size:1.1rem;font-weight:600;letter-spacing:-0.01em;">智能体协作</div>
            <div style="font-size:0.85rem;opacity:0.85;margin-top:0.3rem;">多角色并行 · 智能路由</div>
        </div>
        """, unsafe_allow_html=True)

    with entry_col:
        st.markdown('<div style="text-align:center;padding:0.5rem 0;"><span style="font-size:1.8rem;">📋</span><br><span style="font-weight:600;font-size:1rem;color:#1d1d1f;">录入节点</span></div>', unsafe_allow_html=True)
        st.caption("任务解析 & 数据录入")
    with review_col:
        st.markdown('<div style="text-align:center;padding:0.5rem 0;"><span style="font-size:1.8rem;">🔍</span><br><span style="font-weight:600;font-size:1rem;color:#1d1d1f;">审核节点</span></div>', unsafe_allow_html=True)
        st.caption("风险识别 & 合规检查")
    with analysis_col:
        st.markdown('<div style="text-align:center;padding:0.5rem 0;"><span style="font-size:1.8rem;">📊</span><br><span style="font-weight:600;font-size:1rem;color:#1d1d1f;">分析节点</span></div>', unsafe_allow_html=True)
        st.caption("智能分析 & 周报生成")

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
