#!/usr/bin/env python3
"""直接测试 DashScope ASR 转写，验证轮询逻辑"""
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import dashscope
from dashscope.audio.asr import Transcription

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    print("ERROR: DASHSCOPE_API_KEY not set")
    sys.exit(1)

# 使用已上传到 OSS 的音频 URL（从之前的 recording 获取）
# 这里我们需要一个有效的 OSS 签名 URL
from src.services.oss_service import get_oss_service
from src.db import get_db
from src.services.recording_service import RecordingService

db = next(get_db())
rec_service = RecordingService(db)
rec = rec_service.get_recording("local-test-device_20260106_200309")

if not rec:
    print("ERROR: Recording not found")
    sys.exit(1)

oss = get_oss_service()
download_url = oss.sign_url_for_key("GET", rec.oss_file_path, 3600)
print(f"Using audio URL: {download_url[:80]}...")

# 提交转写任务
print("\n1. Submitting transcription task...")
task_response = Transcription.async_call(
    model='paraformer-v1',
    file_urls=[download_url]
)
task_id = task_response.output.task_id
print(f"Task ID: {task_id}")

# 轮询等待完成
print("\n2. Polling for completion (max 10 minutes)...")
start_time = time.time()
max_wait = 600  # 10 minutes
poll_interval = 5  # 5 seconds

while True:
    resp = Transcription.fetch(task=task_id)
    output = resp.output
    task_status = output.get("task_status")
    
    elapsed = time.time() - start_time
    print(f"  [{elapsed:.1f}s] Status: {task_status}")
    
    if task_status == "SUCCEEDED":
        print("\n3. Task succeeded! Parsing results...")
        results = output.get("results") or []
        if results:
            first = results[0] or {}
            sentences = first.get("sentences") or []
            print(f"   Found {len(sentences)} segments")
            
            # 显示前 3 个片段
            for i, s in enumerate(sentences[:3]):
                print(f"   [{i}] {s.get('text', '')[:50]}...")
            
            if len(sentences) > 3:
                print(f"   ... and {len(sentences) - 3} more segments")
            
            # 检查 transcription_url
            transcription_url = first.get("transcription_url")
            if transcription_url:
                print(f"\n   Also found transcription_url: {transcription_url[:80]}...")
                print("   Downloading and parsing...")
                import httpx
                with httpx.Client(timeout=60.0) as client:
                    r = client.get(transcription_url)
                    r.raise_for_status()
                    detail = r.json()
                    print(f"   JSON keys: {list(detail.keys())}")
                    
                    # 尝试多种可能的字段路径
                    sents = (
                        detail.get("transcripts")
                        or detail.get("sentences")
                        or detail.get("Sentences")
                        or detail.get("result", {}).get("sentences")
                        or detail.get("data", {}).get("sentences")
                        or []
                    )
                    print(f"   Found {len(sents)} sentences from URL")
                    if sents and len(sents) > 0:
                        print(f"   First sentence keys: {list(sents[0].keys())}")
                        print(f"   First sentence: {sents[0]}")
                    else:
                        print(f"   Full JSON structure: {detail}")
        
        break
    elif task_status == "FAILED":
        print(f"\nERROR: Task failed: {output.get('message', 'unknown error')}")
        sys.exit(1)
    
    if elapsed > max_wait:
        print(f"\nERROR: Timeout after {max_wait}s")
        sys.exit(1)
    
    time.sleep(poll_interval)

print("\n✅ Test completed successfully!")
