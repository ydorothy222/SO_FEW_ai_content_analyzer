from typing import Any, Dict, List, Optional

from openai import OpenAI

from src.config import get_settings


class LLMService:
    """
    使用 DashScope 的 OpenAI 兼容接口与 Qwen 模型进行分析。

    这里只定义接口形状：
    - analyze(transcript_segments) -> analysis_json
    """

    def __init__(self) -> None:
        settings = get_settings().dashscope
        self.model = settings.llm_model
        self.client = OpenAI(
            api_key=settings.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def analyze(self, transcript_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        # TODO: 根据 CURSORRULE 设计 prompt，返回结构化 JSON
        return {}


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


