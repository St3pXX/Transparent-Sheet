"""
飞书 API 客户端 — 基于 lark-oapi SDK。

令牌桶限流（全局 QPS=20）、分批写入多维表格（每批 10 条），
使用 lark-oapi 原生异步方法 abatch_create。
"""
import asyncio
import time
from typing import Any

from lark_oapi import Client
from lark_oapi.api.bitable.v1 import (
    BatchCreateAppTableRecordRequest,
    BatchCreateAppTableRecordRequestBody,
    AppTableRecord,
)
from lark_oapi.api.bitable.v1.model.batch_create_app_table_record_response import (
    BatchCreateAppTableRecordResponse,
)

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
    """统一的飞书 API 客户端。"""

    def __init__(self, app_id: str, app_secret: str, qps: int = 20):
        self.app_id = app_id
        self.app_secret = app_secret
        self.qps = qps
        self._rate_limiter = TokenBucketRateLimiter(qps=qps)
        self._client = (
            Client.builder()
            .app_id(app_id)
            .app_secret(app_secret)
            .build()
        )

    async def batch_create_records(
        self, app_token: str, table_id: str, records: list[dict[str, Any]]
    ) -> list[str]:
        """
        分批写入多维表格记录（每批最多 10 条）。

        Args:
            app_token: 多维表格的 app_token
            table_id: 目标数据表的 table_id
            records: 记录列表，每条记录格式为 {"fields": {"字段名": 值, ...}}

        Returns:
            创建成功的 record_id 列表

        Raises:
            FeishuAPIError: API 调用失败时抛出
        """
        created_ids: list[str] = []
        batch_size = 10

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            ids = await self._batch_create_batch(app_token, table_id, batch)
            created_ids.extend(ids)

        return created_ids

    async def _batch_create_batch(
        self, app_token: str, table_id: str, records: list[dict[str, Any]]
    ) -> list[str]:
        """写入一批记录（最多 10 条）。"""
        await self._rate_limiter.acquire()

        app_table_records = [
            AppTableRecord.builder().fields(r.get("fields", {})).build()
            for r in records
        ]

        body = (
            BatchCreateAppTableRecordRequestBody.builder()
            .records(app_table_records)
            .build()
        )

        request = (
            BatchCreateAppTableRecordRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .request_body(body)
            .build()
        )

        response: BatchCreateAppTableRecordResponse = (
            await self._client.bitable.v1.app_table_record.abatch_create(request)
        )

        if not response.success():
            raise FeishuAPIError(
                code=response.code,
                msg=response.msg,
                raw=response.raw,
            )

        record_ids = []
        if response.data and response.data.records:
            for record in response.data.records:
                if record.record_id:
                    record_ids.append(record.record_id)

        return record_ids
