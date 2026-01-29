#!/usr/bin/env python3
"""
测试用户次数控制是否生效：
- 游客：前 3 次成功(200)，第 4 次 402
- 普通用户余额 0：第 1 次即 402
- 管理员：多次均 200（不扣次数）
需先启动服务：uvicorn src.main:app --port 8000
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

import httpx

BASE = "http://127.0.0.1:8000"
TIMEOUT = 10


def test_guest_3_then_402():
    """游客：3 次成功，第 4 次 402。"""
    print("\n1. 游客：前 3 次 200，第 4 次 402")
    client = httpx.Client(base_url=BASE, timeout=TIMEOUT, follow_redirects=True)
    r = client.get("/v1/auth/me")
    if r.status_code != 200:
        print(f"   失败: GET /auth/me -> {r.status_code}")
        return False
    data = r.json()
    if data.get("type") != "guest" or data.get("remaining") != 3:
        print(f"   失败: 期望 type=guest remaining=3，得到 {data}")
        return False
    print(f"   已创建游客，剩余 {data['remaining']} 次")

    for i in range(4):
        r = client.post("/v1/content-workflow/deduct-one", json={})
        if i < 3:
            if r.status_code != 200:
                print(f"   第 {i+1} 次期望 200，得到 {r.status_code} {r.text}")
                return False
            print(f"   第 {i+1} 次: 200 OK")
        else:
            if r.status_code != 402:
                print(f"   第 4 次期望 402，得到 {r.status_code} {r.text}")
                return False
            print(f"   第 4 次: 402 已限制")
    print("   通过")
    return True


def test_user_zero_balance_402():
    """普通用户余额 0：第 1 次即 402。"""
    print("\n2. 普通用户(余额=0)：第 1 次应 402")
    client = httpx.Client(base_url=BASE, timeout=TIMEOUT, follow_redirects=True)
    email = "quota_test_user@example.com"
    password = "test123456"
    r = client.post("/v1/auth/register", json={"email": email, "password": password})
    if r.status_code != 200:
        # 可能已注册过，尝试登录
        r = client.post("/v1/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        print(f"   失败: 注册/登录 -> {r.status_code} {r.text}")
        return False
    print("   已登录普通用户(余额=0)")

    r = client.post("/v1/content-workflow/deduct-one", json={})
    if r.status_code != 402:
        print(f"   期望 402，得到 {r.status_code} {r.text}")
        return False
    print("   第 1 次: 402 已限制")
    print("   通过")
    return True


def test_admin_unlimited():
    """管理员：多次均 200。"""
    print("\n3. 管理员：多次调用均 200")
    client = httpx.Client(base_url=BASE, timeout=TIMEOUT, follow_redirects=True)
    r = client.post(
        "/v1/auth/login",
        json={"email": "YANGRONG", "password": "YANGRONG"},
    )
    if r.status_code != 200:
        print(f"   失败: 管理员登录 -> {r.status_code} {r.text}")
        return False
    print("   已登录管理员")

    for i in range(3):
        r = client.post("/v1/content-workflow/deduct-one", json={})
        if r.status_code != 200:
            print(f"   第 {i+1} 次期望 200，得到 {r.status_code} {r.text}")
            return False
        print(f"   第 {i+1} 次: 200 OK")
    print("   通过")
    return True


def main():
    print("========== 用户次数控制测试 ==========")
    print("请确保服务已启动: uvicorn src.main:app --port 8000")

    ok = True
    try:
        r = httpx.get(f"{BASE}/health", timeout=2)
        if r.status_code != 200:
            print("服务未就绪或未启动")
            sys.exit(1)
    except Exception as e:
        print(f"无法连接服务: {e}")
        sys.exit(1)

    ok &= test_guest_3_then_402()
    ok &= test_user_zero_balance_402()
    ok &= test_admin_unlimited()

    print("\n========== 结果 ==========")
    if ok:
        print("全部通过：游客 3 次后限制、普通用户 0 余额限制、管理员不限。")
    else:
        print("存在失败用例。")
        sys.exit(1)


if __name__ == "__main__":
    main()
