"""
TransparentSheet 控制台（Streamlit UI）

所有 LangGraph 执行逻辑在 FastAPI 后端（transparent_sheet.api.server）。
这里只做两件事：
1. 显示任务输入框
2. 通过 SSE 调用后端，执行 → 展示结果 → 确认写入飞书
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import uuid
import threading
import time

import streamlit as st

st.set_page_config(
    page_title="TransparentSheet 控制台",
    page_icon="✨",
    layout="wide",
)

# =============================================================================
# 常量 & 状态
# =============================================================================
BACKEND = "http://localhost:8000"

# ---- Streamlit CSS ----
st.markdown("""
<style>
.stApp { background: #f0f2f5; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
h1 { color: #1a1a2e; font-weight: 700; letter-spacing: -0.03em; }
.agent-card {
    background: white; border-radius: 16px; padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07); text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.agent-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
.status-badge {
    display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600; margin-top: 0.5rem;
}
.status-running { background: #e8f0fe; color: #1a73e8; }
.status-success { background: #e6f4ea; color: #34a853; }
.status-error   { background: #fce8e6; color: #ea4335; }
.status-waiting { background: #fef7e0; color: #f9a825; }
.status-pending { background: #f3f4f6; color: #6b7280; }
.status-confirming { background: #f3e8ff; color: #9333ea; }
.result-card {
    background: white; border-radius: 12px; padding: 1.25rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin-bottom: 0.75rem;
}
.report-box {
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
    padding: 1rem; white-space: pre-wrap; font-size: 0.875rem;
    max-height: 400px; overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# ---- Session State 初始化 ----
if "task_id" not in st.session_state:
    st.session_state.task_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []
if "agent_status" not in st.session_state:
    st.session_state.agent_status = {}
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "task_status" not in st.session_state:
    st.session_state.task_status = "idle"  # idle|running|confirming|done|error
if "task_input_val" not in st.session_state:
    st.session_state.task_input_val = ""

# =============================================================================
# 侧边栏
# =============================================================================
with st.sidebar:
    st.title("⚙️ 配置")

    # 健康检查
    try:
        resp = urllib.request.urlopen(f"{BACKEND}/health", timeout=3)
        health = json.loads(resp.read())
        st.success(f"✅ 后端在线  Graph: {health.get('graph')}  Store: {health.get('store')}")
    except Exception:
        st.error("❌ 后端未连接  请先启动 python -m uvicorn transparent_sheet.api.server:app --port 8000")

    st.divider()

    if st.button("🔄 重置会话", use_container_width=True):
        st.session_state.task_id = str(uuid.uuid4())
        st.session_state.agent_status = {}
        st.session_state.last_result = None
        st.session_state.task_status = "idle"
        st.session_state.task_input_val = ""
        st.rerun()

    st.divider()
    st.markdown("**操作流程**")
    st.markdown("""
    1. 输入运营任务
    2. 点击「🚀 执行分析」
    3. 查看分析结果
    4. 确认后写入飞书
    """)

# =============================================================================
# 主界面
# =============================================================================
st.title("TransparentSheet 多智能体运营平台")
st.caption("基于 LangGraph + DeepSeek + 飞书多维表格的多 Agent 协作系统")

# ---- 任务输入 ----
with st.container():
    c1, c2 = st.columns([6, 1])
    with c1:
        task_input = st.text_area(
            "📝 输入运营任务",
            placeholder="例如：补全本周销售数据并生成运营周报",
            value=st.session_state.task_input_val,
            label_visibility="collapsed",
            key="task_area",
        )
    with c2:
        st.write("")
        run_btn = st.button("🚀 执行分析", type="primary", use_container_width=True)

# =============================================================================
# Agent 状态看板
# =============================================================================
st.markdown("### 🤖 Agent 执行状态")

AGENTS = [
    ("📋", "Entry",     "录入 & 数据补全"),
    ("🔍", "Review",   "质量审核"),
    ("📊", "Analysis", "销售分析"),
    ("⚠️",  "Risk",     "风险检测"),
    ("📝", "Report",   "汇总报告"),
]
cols = st.columns(len(AGENTS))

for i, (icon, name, desc) in enumerate(AGENTS):
    status = st.session_state.agent_status.get(name.lower(), "pending")
    badge_cls = f"status-{status}"
    with cols[i]:
        st.markdown(f"""
        <div class="agent-card">
            <div style="font-size:2rem;margin-bottom:0.5rem;">{icon}</div>
            <div style="font-weight:700;font-size:1rem;">{name}</div>
            <div style="color:#6b7280;font-size:0.75rem;">{desc}</div>
            <br>
            <span class="status-badge {badge_cls}">{status.upper()}</span>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# 执行逻辑 — 在主线程运行，不在 async 中
# =============================================================================
def run_task(task_id: str, task_input: str):
    """通过 HTTP SSE 调用后端，更新 session_state"""
    import urllib.request

    url = f"{BACKEND}/stream/{task_id}?input={urllib.parse.quote(task_input)}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                raw = json.loads(line[6:])
                event_type = raw.get("type", "")
                data = raw.get("data", {})

                if event_type == "state":
                    # 更新 agent status
                    new_status = data.get("agent_status", {})
                    st.session_state.agent_status = new_status
                    st.session_state.last_result = data
                    st.rerun()

                elif event_type in ("confirm_required", "waiting_confirm"):
                    st.session_state.task_status = "confirming"
                    st.session_state.last_result = data
                    st.rerun()

                elif event_type == "done":
                    st.session_state.task_status = "done"
                    st.session_state.agent_status = data.get("agent_status", {})
                    st.session_state.last_result = data
                    st.rerun()

                elif event_type == "error":
                    st.session_state.task_status = "error"
                    st.session_state.last_result = {"error": data.get("message", str(data))}
                    st.rerun()

    except Exception as e:
        st.session_state.task_status = "error"
        st.session_state.last_result = {"error": str(e)}
        st.rerun()


if run_btn and task_input.strip():
    st.session_state.task_id = str(uuid.uuid4())
    st.session_state.task_input_val = task_input
    st.session_state.agent_status = {}
    st.session_state.last_result = None
    st.session_state.task_status = "running"
    st.rerun()

    # 后台线程执行 HTTP 请求，避免阻塞 Streamlit
    t = threading.Thread(target=run_task, args=(st.session_state.task_id, task_input), daemon=True)
    t.start()

# ---- 正在运行中 ----
if st.session_state.task_status == "running":
    st.info("🤖 Agent 执行中，请稍候...")

# =============================================================================
# 结果展示 & 确认区
# =============================================================================
if st.session_state.last_result:
    result = st.session_state.last_result

    # ---- 报告内容 ----
    report = result.get("report_content", "")
    if report:
        st.markdown("**📋 运营周报：**")
        st.markdown(f'<div class="report-box">{report[:3000]}</div>', unsafe_allow_html=True)
        if len(report) > 3000:
            st.caption(f"（内容较长，已截取前 3000 字符，全长 {len(report)} 字符）")

    # ---- 分析摘要 ----
    summary = result.get("analysis_summary", "")
    if summary:
        with st.expander("📊 分析摘要（点击展开）"):
            st.markdown(summary)

    # ---- 风险等级 ----
    risk_levels = result.get("risk_levels", {})
    if risk_levels:
        with st.expander("⚠️ 风险检测结果（点击展开）"):
            for rec_id, level in risk_levels.items():
                color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(level, "⚪")
                st.markdown(f"  {color} `{rec_id}` — {level}")

    st.divider()

    # ---- 确认区 ----
    if st.session_state.task_status == "confirming":
        st.warning("⏳ 等待确认 — 分析完成，请审核后确认写入飞书")

    col_confirm, col_reset = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认写入飞书", type="primary", use_container_width=True):
            _tid = st.session_state.task_id
            _url = f"{BACKEND}/confirm/{_tid}?action=confirm"

            try:
                req = urllib.request.Request(_url)
                with urllib.request.urlopen(req, timeout=120) as resp:
                    for line in resp:
                        line = line.decode("utf-8").strip()
                        if not line.startswith("data: "):
                            continue
                        raw = json.loads(line[6:])
                        if raw.get("type") == "done":
                            st.session_state.task_status = "done"
                            st.session_state.last_result = raw.get("data", {})
                            writeback_msg = raw["data"].get("agent_outputs", {}).get("writeback", "写入完成")
                            st.session_state.last_result = raw["data"]
                            st.rerun()
                        elif raw.get("type") == "error":
                            st.error(f"❌ 写入失败：{raw['data'].get('message')}")
                            st.rerun()
            except urllib.error.URLError as e:
                st.error(f"❌ 无法连接后端：{e}")
            except Exception as e:
                st.error(f"❌ 写入失败：{e}")

    with col_reset:
        st.write("")
        if st.button("🔄 重新开始", use_container_width=True):
            st.session_state.task_id = str(uuid.uuid4())
            st.session_state.agent_status = {}
            st.session_state.last_result = None
            st.session_state.task_status = "idle"
            st.session_state.task_input_val = ""
            st.rerun()

# ---- 错误展示 ----
if st.session_state.task_status == "error" and st.session_state.last_result:
    err = st.session_state.last_result.get("error", "未知错误")
    st.error(f"❌ 执行出错：{err}")

# ---- 历史记录 ----
if st.session_state.history:
    with st.expander("📜 最近任务", expanded=False):
        for item in reversed(st.session_state.history[-5:]):
            st.text(f"[{item['time']}] {item['task'][:50]} — {item['status']}")

# ---- 空状态提示 ----
if st.session_state.task_status == "idle" and not st.session_state.last_result:
    st.info("👆 在上方输入运营任务，点击「🚀 执行分析」开始")
