import asyncio
import time

class TokenBucketRateLimiter:
    """简单令牌桶限流器。"""
    def __init__(self, qps: int):
        self.qps = qps
        self.interval = 1.0 / qps
        self.last_token = 0.0

    async def acquire(self):
        now = time.time()
        wait = self.last_token + self.interval - now
        if wait > 0:
            await asyncio.sleep(wait)
        self.last_token = time.time()


class FeishuApiClient:
    def __init__(self, app_id: str, app_secret: str, qps: int = 20):
        self.app_id = app_id
        self.app_secret = app_secret
        self.qps = qps
        self._rate_limiter = TokenBucketRateLimiter(qps)
        self._semaphore = asyncio.Semaphore(10)
        self._tenant_token: str | None = None
        self._token_expires_at: float = 0
        self._token_lock = asyncio.Lock()

    async def _get_tenant_token(self) -> str:
        async with self._token_lock:
            if time.time() >= self._token_expires_at:
                self._tenant_token = await self._fetch_token()
                self._token_expires_at = time.time() + 7200
            return self._tenant_token

    async def _fetch_token(self) -> str:
        # 真实实现：POST 到飞书 OAuth 端点
        # Phase 1 返回 mock token
        return "mock-token"

    async def _do_request(self, method: str, url: str, **kwargs) -> dict:
        # 占位 — 真实实现调用飞书 API
        return {"data": {"records": []}}

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        await self._rate_limiter.acquire()
        await self._semaphore.acquire()
        try:
            from .exceptions import Feishu429Error, FeishuAPIError
            for attempt in range(3):
                try:
                    return await self._do_request(method, url, **kwargs)
                except Feishu429Error as e:
                    retry_after = e.retry_after or (2 ** attempt)
                    await asyncio.sleep(retry_after)
                    continue
            raise FeishuAPIError("Max retries exceeded")
        finally:
            self._semaphore.release()

    async def batch_create_records(self, table_id: str, records: list[dict]) -> list[str]:
        BATCH_SIZE = 10
        created_ids = []
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            result = await self._request(
                "POST",
                f"/bitable/v1/apps/{table_id}/tables/records/batch_create",
                json={"records": batch}
            )
            created_ids.extend([r["record_id"] for r in result["data"]["records"]])
        return created_ids
