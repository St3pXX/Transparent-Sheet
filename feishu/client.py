"""
飞书 API 客户端 — 基于 lark-oapi SDK。

令牌桶限流（全局 QPS=20）、分批写入多维表格（每批 10 条），
使用 lark-oapi 原生异步方法 abatch_create。
自动发现并创建所需字段。
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
from lark_oapi.api.bitable.v1.model.app_table_field import AppTableField
from lark_oapi.api.bitable.v1.model.create_app_table_field_request import (
    CreateAppTableFieldRequest,
)
from lark_oapi.api.bitable.v1.model.list_app_table_field_request import (
    ListAppTableFieldRequest,
)
from lark_oapi.api.bitable.v1.model.list_app_table_field_response import (
    ListAppTableFieldResponse,
)
from lark_oapi.api.bitable.v1.model.create_app_table_field_response import (
    CreateAppTableFieldResponse,
)

from .exceptions import FeishuAPIError

# 飞书多维表格字段类型（type 编号）
FIELD_TYPE_TEXT = 1
FIELD_TYPE_SINGLE_SELECT = 3


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

    # ------------------------------------------------------------------
    # 字段管理
    # ------------------------------------------------------------------

    async def list_fields(
        self, app_token: str, table_id: str
    ) -> dict[str, str]:
        """
        列出表中所有字段名 → field_id 的映射。

        Returns:
            {"字段名": "field_id", ...}
        """
        req = (
            ListAppTableFieldRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .build()
        )
        resp: ListAppTableFieldResponse = (
            await self._client.bitable.v1.app_table_field.alist(req)
        )
        if not resp.success():
            raise FeishuAPIError(code=resp.code, msg=resp.msg, raw=resp.raw)

        result: dict[str, str] = {}
        if resp.data and resp.data.items:
            for f in resp.data.items:
                if f.field_name and f.field_id:
                    result[f.field_name] = f.field_id
        return result

    async def create_text_field(
        self, app_token: str, table_id: str, field_name: str
    ) -> str:
        """
        创建文本字段，返回 field_id。
        如果字段已存在则返回现有 field_id（静默处理）。
        """
        req = (
            CreateAppTableFieldRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .request_body(
                AppTableField.builder()
                .field_name(field_name)
                .type(FIELD_TYPE_TEXT)
                .build()
            )
            .build()
        )
        resp: CreateAppTableFieldResponse = (
            await self._client.bitable.v1.app_table_field.acreate(req)
        )
        if not resp.success():
            # 可能是字段已存在（错误码 230001），此时直接返回现有 field_id
            if resp.code == 230001:
                # 字段名重复，查找现有 field_id
                existing = await self.list_fields(app_token, table_id)
                if field_name in existing:
                    return existing[field_name]
            raise FeishuAPIError(code=resp.code, msg=resp.msg, raw=resp.raw)

        field_id = ""
        if resp.data and resp.data.field:
            field_id = resp.data.field.field_id or ""
        return field_id

    async def ensure_fields(
        self, app_token: str, table_id: str, field_names: list[str]
    ) -> list[str]:
        """
        确保表中存在指定字段列表（不存在则自动创建），
        返回所有字段的 field_id 列表。
        """
        existing = await self.list_fields(app_token, table_id)
        field_ids: list[str] = []
        for name in field_names:
            if name in existing:
                field_ids.append(existing[name])
            else:
                fid = await self.create_text_field(app_token, table_id, name)
                field_ids.append(fid)
        return field_ids

    # ------------------------------------------------------------------
    # 记录写入
    # ------------------------------------------------------------------

    async def batch_create_records(
        self,
        app_token: str,
        table_id: str,
        records: list[dict[str, Any]],
        auto_create_fields: bool = True,
    ) -> list[str]:
        """
        分批写入多维表格记录（每批最多 10 条）。

        Args:
            app_token: 多维表格的 app_token
            table_id: 目标数据表的 table_id
            records: 记录列表，每条记录格式为 {"fields": {"字段名": 值, ...}}
            auto_create_fields: 是否自动创建不存在的字段（默认 True）

        Returns:
            创建成功的 record_id 列表
        """
        if not records:
            return []

        # 自动发现并创建所需字段
        if auto_create_fields:
            all_field_names = set()
            for rec in records:
                all_field_names.update(rec.get("fields", {}).keys())
            await self.ensure_fields(app_token, table_id, list(all_field_names))

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
