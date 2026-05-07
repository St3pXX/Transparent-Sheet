import streamlit as st
from .base import ConfirmationChannel, ConfirmationResponse
from transparent_sheet.orchestration.state import OrchestrationState

CONFIRMATION_CSS = """
<style>
  .report-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
    border: 1px solid rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
  }
  .report-title {
    font-size: 1.4rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #1d1d1f;
    margin-bottom: 1rem;
  }
  .confirm-label {
    font-size: 1rem;
    font-weight: 500;
    color: #1d1d1f;
    margin-bottom: 0.75rem;
  }
  .warning-item {
    background: rgba(255,149,0,0.08);
    border-left: 3px solid #ff9500;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    color: #1d1d1f;
    font-size: 0.95rem;
  }
  /* Confirm button row */
  [data-testid="stHorizontalBlock"]:has(.confirm-btn) {
    gap: 1rem !important;
  }
  .confirm-btn > button {
    background: #34c759 !important;
    box-shadow: 0 2px 8px rgba(52,199,89,0.25) !important;
  }
  .confirm-btn > button:hover {
    background: #2db84d !important;
    box-shadow: 0 4px 16px rgba(52,199,89,0.35) !important;
  }
  .revise-btn > button {
    background: #ff9500 !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(255,149,0,0.25) !important;
  }
  .revise-btn > button:hover {
    background: #e68600 !important;
    box-shadow: 0 4px 16px rgba(255,149,0,0.35) !important;
  }
  /* Target buttons by position within confirmation horizontal block */
  div[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stButton"] > button {
    background: #34c759 !important;
    box-shadow: 0 2px 8px rgba(52,199,89,0.25) !important;
  }
  div[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stButton"] > button:hover {
    background: #2db84d !important;
    box-shadow: 0 4px 16px rgba(52,199,89,0.35) !important;
  }
  div[data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stButton"] > button {
    background: #ff9500 !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(255,149,0,0.25) !important;
  }
  div[data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stButton"] > button:hover {
    background: #e68600 !important;
    box-shadow: 0 4px 16px rgba(255,149,0,0.35) !important;
  }
</style>
"""


class StreamlitChannel(ConfirmationChannel):
    async def render_confirmation(self, state: OrchestrationState) -> None:
        st.markdown(CONFIRMATION_CSS, unsafe_allow_html=True)
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown('<p class="report-title">📋 报告预览</p>', unsafe_allow_html=True)
        st.markdown(state.get("report_content", ""))
        st.markdown('</div>', unsafe_allow_html=True)

        if state.get("pending_confirmations"):
            st.markdown('<p class="confirm-label">⚠️ 待确认项</p>', unsafe_allow_html=True)
            for item in state["pending_confirmations"]:
                st.markdown(f'<div class="warning-item">⚠️ {item}</div>', unsafe_allow_html=True)

    async def wait_for_response(self) -> ConfirmationResponse:
        col1, col2 = st.columns(2)
        confirm = col1.button("✅ 确认并写入")
        revise = col2.button("✏️ 修改报告")

        if confirm:
            return ConfirmationResponse(action="confirm")
        elif revise:
            return ConfirmationResponse(action="revise", modifications=[])
        else:
            raise RuntimeError("Should not reach here — Streamlit blocks on user input")