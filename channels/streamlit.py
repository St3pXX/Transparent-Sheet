import streamlit as st
from .base import ConfirmationChannel, ConfirmationResponse
from transparent_sheet.orchestration.state import OrchestrationState

class StreamlitChannel(ConfirmationChannel):
    async def render_confirmation(self, state: OrchestrationState) -> None:
        st.divider()
        st.subheader("📋 报告预览")
        st.markdown(state.get("report_content", ""))

        if state.get("pending_confirmations"):
            st.subheader("⚠️ 待确认项")
            for item in state["pending_confirmations"]:
                st.warning(item)

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