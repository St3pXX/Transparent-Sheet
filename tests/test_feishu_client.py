import pytest
import asyncio
from unittest.mock import AsyncMock, patch
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
    # Mock _batch_create_batch 避免真实 HTTP 调用
    with patch.object(client, "_batch_create_batch", new_callable=AsyncMock) as mock_batch:
        mock_batch.return_value = ["rec_001", "rec_002"]
        # 同时 mock ensure_fields 避免真实 API 调用
        with patch.object(client, "ensure_fields", new_callable=AsyncMock):
            ids = await client.batch_create_records(
                "app-token", "table-1", [{"fields": {"a": 1}}, {"fields": {"b": 2}}],
            )
    assert ids == ["rec_001", "rec_002"]
    mock_batch.assert_called_once()
