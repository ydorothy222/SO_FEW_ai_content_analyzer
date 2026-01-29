import json
import sys

import httpx


def main():
    recording_id = "local-test-device_20260106_200309"
    question = "请总结这段对话，并指出可能不恰当的沟通点，给出改进建议。"

    url = "http://127.0.0.1:8000/v1/pipeline/full-test"
    with httpx.Client(timeout=600.0) as client:
        resp = client.post(url, json={"recording_id": recording_id, "question": question})
    print("status:", resp.status_code)
    
    if resp.status_code >= 400:
        print(resp.text)
        sys.exit(1)
    
    # 解析 JSON 并打印关键信息
    data = resp.json()
    result = data.get("data", {})
    print(f"\n[SUCCESS]")
    print(f"Recording ID: {result.get('recording_id')}")
    print(f"Status: {result.get('status')}")
    print(f"Segments saved: {result.get('segments_saved')}")
    print(f"Analysis version: {result.get('analysis_version')}")
    answer = result.get('answer', '')
    print(f"\nAnswer ({len(answer)} chars):")
    # 安全打印，避免编码问题
    try:
        print(answer[:1000])
    except UnicodeEncodeError:
        # 如果遇到编码问题，只打印 ASCII 部分
        safe_answer = answer.encode('ascii', errors='ignore').decode('ascii')
        print(safe_answer[:1000])
    if len(answer) > 1000:
        print(f"... (truncated, total {len(answer)} chars)")


if __name__ == "__main__":
    main()


