from transparent_sheet.agents.tools.demo_data import create_demo_records, create_demo_risk_data

def test_create_demo_records_count():
    records = create_demo_records(15)
    assert len(records) == 15
    assert "日期" in records[0]
    assert "商品" in records[0]

def test_create_demo_risk_data():
    risks = create_demo_risk_data()
    assert len(risks) == 5
    assert risks[0]["level"] in ["high", "medium", "low"]