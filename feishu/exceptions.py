class FeishuAPIError(Exception):
    """通用飞书 API 错误。"""
    pass

class Feishu429Error(FeishuAPIError):
    """限流错误 — 遵循 Retry-After 头。"""
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after
