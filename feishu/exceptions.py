class FeishuAPIError(Exception):
    """通用飞书 API 错误。"""
    def __init__(self, code: int | None = None, msg: str = "", raw=None):
        self.code = code
        self.msg = msg
        self.raw = raw
        super().__init__(f"FeishuAPIError {code}: {msg}")

class Feishu429Error(FeishuAPIError):
    """限流错误 — 遵循 Retry-After 头。"""
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after
