"""
LLM 配置模块
统一管理所有 Agent 的 LLM 初始化
支持环境变量配置
"""
import os
from langchain_openai import ChatOpenAI

# 默认值（从环境变量读取）
API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.minimax.chat/v1")
MODEL = os.getenv("OPENAI_MODEL", "MiniMax-M2.5")

def get_llm(model: str = None, temperature: float = 0.7) -> ChatOpenAI:
    """
    获取 LLM 实例

    Args:
        model: 模型名称，默认使用环境变量 OPENAI_MODEL
        temperature: 温度参数

    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=model or MODEL,
        base_url=BASE_URL,
        api_key=API_KEY,
        temperature=temperature,
    )
