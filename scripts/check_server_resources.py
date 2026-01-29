#!/usr/bin/env python3
"""
在本地启动服务并模拟请求，采样内存与 CPU，评估 4 vCPU / 8 GiB 是否够用。
不调用 LLM（不消耗 DASHSCOPE），仅测试 FastAPI + SQLite + 路由与 DB 开销。
"""
import sys
import time
import subprocess
from pathlib import Path

# 确保项目根在 path 中
_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

try:
    import psutil
except ImportError:
    print("请先安装 psutil: pip install psutil")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("请先安装 httpx: pip install httpx")
    sys.exit(1)


BASE_URL = "http://127.0.0.1:8000"
WAIT_READY_SEC = 20
REQUEST_COUNT = 15
SAMPLE_INTERVAL = 0.2


def wait_ready():
    for _ in range(WAIT_READY_SEC * 2):
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def sample_process(proc):
    try:
        p = psutil.Process(proc.pid)
        mem = p.memory_info()
        cpu = p.cpu_percent(interval=0.1)
        return mem.rss, cpu
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None, None


def main():
    print("启动 uvicorn (单 worker)...")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=str(_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_ready():
            print("服务未在限定时间内就绪（请检查端口 8000 是否被占用、.env 是否配置正确）")
            print("参考结论：4 vCPU / 8 GiB 对本产品通常够用，详见 docs/DEPLOY_RESOURCES.md")
            sys.exit(1)
        print("服务已就绪，开始压测与采样...")

        mem_samples = []
        cpu_samples = []

        with httpx.Client(timeout=10) as client:
            for i in range(REQUEST_COUNT):
                try:
                    client.get(f"{BASE_URL}/health")
                    client.get(f"{BASE_URL}/v1/content-workflow/workflow")
                    client.get(f"{BASE_URL}/v1/auth/me")  # 可能 Set-Cookie，带 Cookie 再请求一次
                    client.get(f"{BASE_URL}/v1/auth/me", cookies=client.cookies)
                except Exception as e:
                    print(f"  请求异常: {e}")
                rss, cpu = sample_process(proc)
                if rss is not None:
                    mem_samples.append(rss)
                if cpu is not None:
                    cpu_samples.append(cpu)
                time.sleep(SAMPLE_INTERVAL)

        if not mem_samples:
            print("未能采样到进程内存")
        else:
            rss_mb = [x / (1024 * 1024) for x in mem_samples]
            avg_mb = sum(rss_mb) / len(rss_mb)
            max_mb = max(rss_mb)
            avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            max_cpu = max(cpu_samples) if cpu_samples else 0

            print()
            print("========== 资源采样结果 ==========")
            print(f"  内存 RSS  平均: {avg_mb:.1f} MiB  峰值: {max_mb:.1f} MiB")
            print(f"  CPU 使用 平均: {avg_cpu:.1f}%  峰值: {max_cpu:.1f}%")
            print()

            # 4 vCPU, 8 GiB 评估
            ram_gib = 8
            vcpu = 4
            headroom_mb = (ram_gib * 1024) - max_mb
            print("========== 4 vCPU / 8 GiB 评估 ==========")
            pct_ram = 100 * max_mb / (ram_gib * 1024)
            if max_mb < ram_gib * 1024 * 0.5 and (not cpu_samples or max_cpu < vcpu * 100 * 0.6):
                print("  结论: 够用。")
            elif pct_ram < 70:
                print("  结论: 一般够用，建议预留 1–2 GiB 给系统与 LLM 调用。")
            else:
                print("  结论: 峰值偏高，建议监控或升级配置。")
            print(f"  当前峰值内存约占 8 GiB 的 {pct_ram:.1f}%")
            print()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("服务已停止。")


if __name__ == "__main__":
    main()
