import pytest
import asyncio
from transparent_sheet.feishu.client import TokenBucketRateLimiter, FeishuApiClient

def test_token_bucket_rate_limiter():
    limiter = TokenBucketRateLimiter(qps=5)
    asyncio.get_event_loop().run_until_complete(limiter.acquire())
    asyncio.get_event_loop().run_until_complete(limiter.acquire())
    assert limiter.qps == 5

def test_client_instantiation():
    client = FeishuApiClient("app-id", "app-secret", qps=20)
    assert client.app_id == "app-id"
    assert client.qps == 20

@pytest.mark.asyncio
async def test_batch_create_records():
    client = FeishuApiClient("app-id", "app-secret", qps=20)
    ids = await client.batch_create_records("table-1", [{"a": 1}, {"b": 2}])
    assert isinstance(ids, list)
