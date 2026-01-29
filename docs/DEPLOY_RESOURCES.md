# 4 vCPU / 8 GiB 服务器是否够用

## 结论：**够用**

本产品为 FastAPI + SQLite + 远程 DashScope（转写/LLM），无本地大模型或重型计算，单机 4 vCPU、8 GiB 内存足以支撑中小规模 ToC 使用。

---

## 典型资源占用（参考）

| 组件 | 内存 | CPU |
|------|------|-----|
| FastAPI + Uvicorn 单 worker | ~80–200 MiB RSS | 空闲时接近 0%，请求时短暂 5–20% |
| SQLite | 已含在上述进程内 | 可忽略 |
| DashScope 调用 | **不占本机**（走网络，等待时仅维持连接） | 等待期间几乎不占 CPU |

- **单进程峰值**：约 150–300 MiB（视请求量略有波动）。
- **8 GiB 内存**：系统 + 本服务通常仍余 6 GiB+，足够再跑 Nginx、监控等。
- **4 vCPU**：多数时间为 I/O 等待（数据库、HTTP 客户端），CPU 使用率通常较低；并发高时单 worker 可能成为瓶颈，可酌情增至 2 worker（仍远低于 4 核）。

---

## 自测方法（可选）

在**能正常启动服务**的环境下（含 `.env` 等），在项目根目录执行：

```bash
pip install psutil
python scripts/check_server_resources.py
```

脚本会：

1. 启动一次 uvicorn（单 worker）
2. 对 `/health`、`/v1/auth/me`、`/v1/content-workflow/workflow` 做多轮请求
3. 采样进程内存与 CPU
4. 打印“4 vCPU / 8 GiB 评估”结论

**注意**：脚本**不调用 LLM**（不消耗 DashScope 额度），只测应用与 DB 开销。实际生产若开启多 worker 或并发更高，可按比例预留更多内存（例如 2 worker 预留约 400–600 MiB）。

---

## 部署建议（4 vCPU / 8 GiB）

- **Worker**：先使用 1 个 uvicorn worker，观察 CPU；若经常打满可改为 2。
- **内存**：为系统与未来扩展预留 1–2 GiB，本服务占用远低于 8 GiB。
- **反向代理**：前接 Nginx/Caddy 做静态与 HTTPS，不增加明显资源负担。
- **监控**：用 `top`/`htop` 或云监控观察 RSS 与 CPU，便于后续调优。
