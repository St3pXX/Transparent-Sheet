import pytest

def test_entry_agent_output_structure():
    from transparent_sheet.agents.entry import build_entry_agent
    agent = build_entry_agent()
    assert agent is not None

def test_review_agent_output_structure():
    from transparent_sheet.agents.review import build_review_agent
    agent = build_review_agent()
    assert agent is not None

def test_analysis_agent_output_structure():
    from transparent_sheet.agents.analysis import build_analysis_agent
    agent = build_analysis_agent()
    assert agent is not None

def test_risk_agent_output_structure():
    from transparent_sheet.agents.risk import build_risk_agent
    agent = build_risk_agent()
    assert agent is not None

def test_report_agent_output_structure():
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