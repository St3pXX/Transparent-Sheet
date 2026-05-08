"""
飞书 API 客户端 — 基于 larksuiteoapi SDK。

统一封装：
- 令牌桶限流（全局 QPS=20）
- Token 自动刷新（SDK 内置）
- 分批写入多维表格（每批 10 条）
"""
import asyncio
import time

from larksuiteoapi import Config, DOMAIN_FEISHU
from larksuiteoapi.service.bitable.v1 import AppTableRecord, AppTableRecordBatchCreateReqBody

from .exceptions import FeishuAPIError


class TokenBucketRateLimiter:
    """令牌桶限流器。"""
    def __init__(self, qps: int):
        self.qps = qps
        self.interval = 1.0 / qps
        self._last_token = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.time()
            wait = self._last_token + self.interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_token = time.time()


class FeishuApiClient:
    def __init__(self, app_id: str, app_secret: str, qps: int = 20):
        self.app_id = app_id
        self.app_secret = app_secret
        self._rate_limiter = TokenBucketRateLimiter(qps)
        self._semaphore = asyncio.Semaphore(10)

        from larksuiteoapi import app_settings
        settings = app_settings.AppSettings(
            app_type="internal",
            app_id=app_id,
            app_secret=app_secret,
        )
        self._config = Config(
            domain=DOMAIN_FEISHU,
            app_settings=settings,
            log_level=3,
        )

        from larksuiteoapi.service.bitable.v1 import Service as BitableService
        self._bitable = BitableService(self._config)

    async def batch_create_records(
        self, app_token: str, table_id: str, records: list[dict]
    ) -> list[str]:
        """
        分批写入多维表格（每批 10 条）。
        larksuiteoapi SDK 自动处理 token 刷新。
        我们只在外层做限流控制。
        """
        BATCH_SIZE = 10
        created_ids = []

        for i in range(0, len(records), BATCH_SIZE):
            await self._rate_limiter.acquire()
            async with self._semaphore:
                batch = records[i : i + BATCH_SIZE]
                records_to_create = [
                    AppTableRecord(fields=r.get("fields", {}))
                    for r in batch
                ]
                req_body = AppTableRecordBatchCreateReqBody(records=records_to_create)

                resp = self._bitable.app_table_records.batch_create(
                    app_token,
                    table_id,
                    req_body,
                    tenant_key=self.app_id,
                )
                result = resp.new_call()

                if result.code != 0:
                    raise FeishuAPIError(f"batch_create failed: code={result.code} msg={result.msg}")

                created_ids.extend(r.record_id for r in result.data.records)

        return created_ids
