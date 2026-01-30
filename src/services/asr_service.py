from typing import Any, Dict, List, Optional

import dashscope
from dashscope.audio.asr import Transcription
import httpx

from src.config import get_settings


class ASRService:
    """
    DashScope Paraformer 异步转写（录音文件识别）。
    约定：
    - create_transcription_task(file_urls, callback_url?) -> task_id
    - fetch_task(task_id) -> raw output dict
    - wait_transcription(task_id) -> segments[]
    """

    def __init__(self) -> None:
        self.settings = get_settings().dashscope
        dashscope.api_key = self.settings.api_key

    def create_transcription_task(self, file_urls: List[str], callback_url: Optional[str] = None) -> str:
        kwargs: Dict[str, Any] = {"model": self.settings.asr_model, "file_urls": file_urls}
        if callback_url:
            kwargs["callback_url"] = callback_url

        task_response = Transcription.async_call(**kwargs)
        return task_response.output.task_id

    def fetch_task(self, task_id: str) -> Dict[str, Any]:
        resp = Transcription.fetch(task=task_id)
        return resp.output  # type: ignore[return-value]

    def wait_transcription(self, task_id: str, max_wait_seconds: int = 600) -> List[Dict[str, Any]]:
        """
        轮询等待转写任务完成，最多等待 max_wait_seconds 秒。
        """
        import time
        
        start_time = time.time()
        while True:
            resp = Transcription.fetch(task=task_id)
            output = resp.output
            task_status = output.get("task_status")
            
            if task_status == "SUCCEEDED":
                break
            elif task_status == "FAILED":
                raise RuntimeError(f"ASR task {task_id} failed: {output.get('message', 'unknown error')}")
            
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                raise TimeoutError(f"ASR task {task_id} timeout after {max_wait_seconds}s, status={task_status}")
            
            # 每 5 秒轮询一次
            time.sleep(5)

        # DashScope 返回结构可能包含 transcription_url；此处优先尝试 sentences
        segments: List[Dict[str, Any]] = []
        try:
            results = output.get("results") or []
            if results and isinstance(results, list):
                first = results[0] or {}
                sentences = first.get("sentences") or []
                for i, s in enumerate(sentences):
                    segments.append(
                        {
                            "segment_index": i,
                            "start_ms": int(s.get("begin_time", 0)),
                            "end_ms": int(s.get("end_time", 0)),
                            "text": str(s.get("text", "")),
                            "confidence": s.get("confidence"),
                        }
                    )

                # 有些返回不会直接带 sentences，而是给一个 transcription_url（JSON 文件）
                if not segments:
                    transcription_url = first.get("transcription_url")
                    if transcription_url:
                        with httpx.Client(timeout=60.0) as client:
                            r = client.get(transcription_url)
                            r.raise_for_status()
                            detail = r.json()
                        # DashScope 返回的 JSON 结构：
                        # {"transcripts": [{"sentences": [{"begin_time": 150, "end_time": 7510, "text": "..."}, ...]}, ...]}
                        # 或者直接 {"sentences": [...]}
                        transcripts_list = detail.get("transcripts") or []
                        sents = []
                        # 遍历 transcripts，提取所有 sentences
                        for transcript in transcripts_list:
                            if isinstance(transcript, dict):
                                nested_sents = transcript.get("sentences") or []
                                sents.extend(nested_sents)
                        
                        # 如果没有 transcripts，尝试直接获取 sentences
                        if not sents:
                            sents = (
                                detail.get("sentences")
                                or detail.get("Sentences")
                                or detail.get("result", {}).get("sentences")
                                or detail.get("data", {}).get("sentences")
                                or []
                            )
                        
                        segment_idx = 0
                        for s in sents:
                            # begin_time/end_time 单位是毫秒（不需要 * 1000）
                            begin_ms = s.get("begin_time") or s.get("BeginTime") or 0
                            end_ms = s.get("end_time") or s.get("EndTime") or 0
                            # 如果是秒，转换为毫秒
                            if begin_ms < 10000:  # 假设如果小于 10000，可能是秒
                                begin_ms = int(begin_ms * 1000)
                            if end_ms < 10000:
                                end_ms = int(end_ms * 1000)
                            
                            segments.append(
                                {
                                    "segment_index": segment_idx,
                                    "start_ms": int(begin_ms),
                                    "end_ms": int(end_ms),
                                    "text": str(s.get("text", s.get("Text", ""))),
                                    "confidence": s.get("confidence", s.get("Confidence")),
                                }
                            )
                            segment_idx += 1
        except Exception as e:
            # 保底：返回空，让上层记录失败原因
            raise RuntimeError(f"Failed to parse ASR segments: {e}") from e

        return segments


_asr_service: Optional[ASRService] = None


def get_asr_service() -> ASRService:
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service


