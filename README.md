## 智能陪伴服务端（MVP）

基于 FastAPI 的服务端，用于接收 ESP32-C3 上传的音频、存储到阿里云 OSS，并通过 DashScope 的 Paraformer 与 Qwen-plus 完成转写和分析，支撑“日常对话回顾与建议”的核心功能。

### 快速开始

**要求**：Python 3.8+（服务器部署也需 3.8+，3.6 会装不上依赖）。

1. 创建并激活虚拟环境（可选）  
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 在项目根目录创建 `.env` 文件（不要提交到 Git），配置环境变量：

```bash
ENV=dev
PORT=8000
PUBLIC_BASE_URL=http://localhost:8000

DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_ASR_MODEL=paraformer-v1
DASHSCOPE_LLM_MODEL=qwen-plus

OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_BUCKET=sofewaccampany
OSS_ACCESS_KEY_ID=your-oss-access-key-id
OSS_ACCESS_KEY_SECRET=your-oss-access-key-secret
OSS_CNAME=
OSS_USE_HTTPS=true
OSS_PREFIX=recordings/

# ToC 用户与用量（可选）
JWT_SECRET=change-me-in-production
ADMIN_USERNAME=YANGRONG
ADMIN_PASSWORD=YANGRONG
GUEST_FREE_QUOTA=3

# 邮件（可选，配置后注册可发欢迎邮件）
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=你的邮箱
SMTP_PASSWORD=授权码
SMTP_SEND_WELCOME_EMAIL=true
```

> 注意：以上值仅为占位示例，真实密钥请从控制台获取并**绝对不要提交到仓库**。生产环境务必修改 `JWT_SECRET`。邮件配置详见 [docs/EMAIL_SETUP.md](docs/EMAIL_SETUP.md)。

4. 启动服务：

```bash
uvicorn src.main:app --reload --port 8000
```

**部署**：4 vCPU / 8 GiB 服务器对本产品足够，详见 [docs/DEPLOY_RESOURCES.md](docs/DEPLOY_RESOURCES.md)。可用 `python scripts/check_server_resources.py` 做本地资源采样测试。

### 目录结构

- `src/main.py`：FastAPI 入口
- `src/api/`：路由与接口定义
- `src/config.py`：配置与环境变量
- `src/db/`：数据库模型与会话管理
- `src/services/oss_service.py`：阿里云 OSS 相关封装
- `src/services/asr_service.py`：DashScope 转写服务封装
- `src/services/llm_service.py`：Qwen-plus 分析服务封装
- `src/services/recording_service.py`：录音元数据与状态流转

### 当前已实现的接口（MVP）

- `POST /v1/recordings`：创建/注册一条录音（包含元数据、recording_id、device_id 等）
- `GET /v1/recordings/{recording_id}`：查询录音状态与元数据
- `POST /v1/oss/upload-url`：获取指定 `recording_id` 的音频上传签名 URL
- `GET /v1/oss/download-url/{recording_id}`：获取音频下载签名 URL
- `POST /v1/recordings/{recording_id}/delete`：一键删除该录音相关数据（音频/转写/分析）
- `POST /v1/transcribe/start`：提交 DashScope 转写任务（返回 task_id）
- `GET /v1/transcribe/query/{task_id}`：查询转写任务状态/输出
- `POST /v1/transcribe/wait-and-save`：等待转写完成并落库 transcript segments
- `POST /v1/analysis/{recording_id}/run`：基于转写结果运行分析并落库
- `GET /v1/analysis/{recording_id}`：获取分析结果
- `POST /v1/qa`：基于多个录音的转写片段进行问答（Qwen-plus）
- `POST /v1/pipeline/full-test`：一键从录音到转写+分析+问答（用于联调测试）

后续可以根据 `CURSORRULE` 持续扩展，如 DashScope 回调、问答接口 `/v1/qa` 等。

---

### ToC：AI 内容永动机（面向终端用户）

面向 C 端的内容工作流：游客 3 次免费体验，用完后需邮箱注册；除管理员外，注册用户需充值后才能继续使用。

**用量规则**

- **游客**：每人 3 次免费（按 Cookie `guest_id` 统计），用完后需注册。
- **管理员**：账号与密码均为 `YANGRONG`（可在 `.env` 中配置 `ADMIN_USERNAME` / `ADMIN_PASSWORD`），不扣次数。
- **普通用户**：注册后余额为 0，需由管理员在「账户」页为其充值后才有可用次数。

**前端入口**

- 首页（工作流）：`http://localhost:8000/` 或 `http://localhost:8000/content-workflow`
- 登录：`/static/login.html`
- 注册：`/static/register.html`
- 账户 / 充值：`/static/account.html`（登录后可见余额；管理员可见用户列表与充值表单）

**API**

- `GET /v1/auth/me`：当前身份与剩余次数（无 Cookie 时会创建游客并 Set-Cookie）
- `POST /v1/auth/register`：邮箱注册
- `POST /v1/auth/login`：登录（支持管理员账号 YANGRONG）
- `POST /v1/auth/logout`：登出
- `GET /v1/admin/users`：管理员列出用户（需登录管理员）
- `POST /v1/admin/add-balance`：管理员为指定用户增加次数
- `POST /v1/content-workflow/skill/1..4`：运行四步 Skill，每次成功调用扣减 1 次用量（需 Cookie 且剩余 > 0）

**测试次数控制**（不调用 LLM）：先启动服务，再在项目根目录执行：

```bash
python scripts/test_quota_control.py
```

脚本会验证：游客前 3 次成功、第 4 次返回 402；普通用户余额为 0 时第 1 次即 402；管理员多次调用均成功。


