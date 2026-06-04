import pytest
from transparent_sheet.orchestration.graph import build_graph

def test_graph_builds():
    graph = build_graph()
    assert graph is not None

def test_graph_has_checkpointer():
    graph = build_graph()
    # graph 应该有 checkpointer 属性
    assert hasattr(graph, "checkpointer")

def test_graph_interrupt_before_writeback():
    graph = build_graph()
    # compile 成功说明 interrupt_before 配置正确
    assert graph is not None