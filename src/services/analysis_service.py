import json
from typing import Any, Dict, List

from src.services.llm_service import get_llm_service


ANALYSIS_JSON_SCHEMA_HINT = """
请输出严格 JSON（不要 Markdown），字段如下：
{
  "summary": "string",
  "people": [{"name": "string", "evidence": [{"segment_index": 0}]}],
  "issues": [{"title": "string", "detail": "string", "evidence": [{"segment_index": 0}]}],
  "suggestions": [{"title": "string", "detail": "string"}],
  "sources": [{"segment_index": 0}]
}
"""


class AnalysisService:
    def analyze_transcript(self, transcript_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        llm = get_llm_service()
        content = "\n".join([f"[{i}] {seg.get('text','')}" for i, seg in enumerate(transcript_segments)])

        prompt = (
            "你是一个严谨的中文沟通分析助手。以下是用户当天的一段对话转写（按片段编号）：\n"
            f"{content}\n\n"
            "任务：总结主要内容，抽取出现的人物（若不确定可省略），指出可能不得当的沟通点，并给出改进建议。"
            + ANALYSIS_JSON_SCHEMA_HINT
        )

        # 这里用 LLMService 的最小实现：如果你希望更严格的 schema 校验，可后续加 jsonschema
        resp = llm.client.chat.completions.create(
            model=llm.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        text = resp.choices[0].message.content or "{}"
        try:
            return json.loads(text)
        except Exception:
            return {"summary": None, "people": [], "issues": [], "suggestions": [], "sources": []}


