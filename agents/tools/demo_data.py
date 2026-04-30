"""
DemoDataProvider — 生成真实的电商 Demo 数据。
独立工具，不嵌入 Agent 逻辑。
由 Entry Agent 使用或在控制台模式下直接注入。
"""
import random
import datetime

def create_demo_records(count: int = 20) -> list[dict]:
    """生成假的电商销售记录。"""
    products = ["T恤", "牛仔裤", "连衣裙", "运动鞋", "帽子", "背包", "围巾", "手套"]
    regions = ["华东", "华南", "华北", "西南", "西北"]
    statuses = ["已完成", "已完成", "已完成", "进行中", "已取消"]

    records = []
    base = datetime.date.today() - datetime.timedelta(days=7)
    for i in range(count):
        day_offset = random.randint(0, 6)
        d = base + datetime.timedelta(days=day_offset)
        records.append({
            "日期": d.isoformat(),
            "商品": random.choice(products),
            "地区": random.choice(regions),
            "销量": random.randint(10, 200),
            "销售额": random.randint(500, 10000),
            "状态": random.choice(statuses),
        })
    return records

def create_demo_risk_data() -> list[dict]:
    """为 Risk Agent 生成 Demo 风险记录。"""
    return [
        {"record_id": f"risk-{i}", "level": random.choice(["high", "medium", "low"]),
         "description": f"风险项{i}"}
        for i in range(5)
    ]