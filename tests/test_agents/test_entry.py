import pytest
from unittest.mock import patch, MagicMock
from langchain_core.language_models.chat_models import BaseChatModel


def _fake_llm(**kwargs):
    """返回一个支持 bind_tools 的 mock LLM，不需要真实 API key。"""
    mock = MagicMock(spec=BaseChatModel)
    mock.bind_tools.return_value = mock
    mock.invoke.return_value = MagicMock(content="模拟 LLM 响应")
    return mock


@patch("transparent_sheet.agents.entry.get_llm", side_effect=_fake_llm)
def test_entry_agent_output_structure(mock_llm):
    from transparent_sheet.agents.entry import build_entry_agent
    agent = build_entry_agent()
    assert agent is not None


@patch("transparent_sheet.agents.review.get_llm", side_effect=_fake_llm)
def test_review_agent_output_structure(mock_llm):
    from transparent_sheet.agents.review import build_review_agent
    agent = build_review_agent()
    assert agent is not None


@patch("transparent_sheet.agents.analysis.get_llm", side_effect=_fake_llm)
def test_analysis_agent_output_structure(mock_llm):
    from transparent_sheet.agents.analysis import build_analysis_agent
    agent = build_analysis_agent()
    assert agent is not None


@patch("transparent_sheet.agents.risk.get_llm", side_effect=_fake_llm)
def test_risk_agent_output_structure(mock_llm):
    from transparent_sheet.agents.risk import build_risk_agent
    agent = build_risk_agent()
    assert agent is not None


@patch("transparent_sheet.agents.report.get_llm", side_effect=_fake_llm)
def test_report_agent_output_structure(mock_llm):
    from transparent_sheet.agents.report import build_report_agent
    agent = build_report_agent()
    assert agent is not None


def test_wrappers_importable():
    from transparent_sheet.agents.wrappers import (
        entry_node_wrapper, review_node_wrapper,
        analysis_node_wrapper, risk_node_wrapper,
        report_node_wrapper,
    )
    assert callable(entry_node_wrapper)
    assert callable(review_node_wrapper)
    assert callable(analysis_node_wrapper)
    assert callable(risk_node_wrapper)
    assert callable(report_node_wrapper)