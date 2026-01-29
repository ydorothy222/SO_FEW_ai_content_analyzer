# 邮件发送配置说明

## 一、已实现能力

- **SMTP 发信**：使用 Python 标准库 `smtplib`，无需额外依赖。
- **注册欢迎邮件**：配置 SMTP 并开启 `SMTP_SEND_WELCOME_EMAIL=true` 后，用户注册成功会收到一封欢迎邮件。
- **通用发信**：`src.services.email_service.send_email(to, subject, body_text, body_html=None)` 可在任意业务中调用。

## 二、环境变量（.env）

在项目根或 `src/.env` 中配置：

```bash
# SMTP 服务器（必填三项：HOST、USER、PASSWORD）
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=你的QQ邮箱@qq.com
SMTP_PASSWORD=QQ邮箱授权码
SMTP_FROM_EMAIL=你的QQ邮箱@qq.com
SMTP_USE_TLS=true

# 注册成功后是否发欢迎邮件
SMTP_SEND_WELCOME_EMAIL=true
```

**说明：**

- `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` 留空时，不会发任何邮件，注册流程照常。
- `SMTP_PORT=465` 一般用 SSL；587 用 STARTTLS，`SMTP_USE_TLS=true`。
- QQ 邮箱：在 QQ 邮箱网页 → 设置 → 账户 → 开启 SMTP 服务 → 生成授权码，用授权码填 `SMTP_PASSWORD`。
- **网易 163**：`SMTP_HOST=smtp.163.com`，`SMTP_PORT=465`（SSL）或 994；在 163 网页 → 设置 → POP3/SMTP/IMAP → 开启 SMTP 服务 → 设置授权码，用**授权码**填 `SMTP_PASSWORD`（不是登录密码）。`SMTP_USER` 填完整邮箱如 `xxx@163.com`。
- 阿里云 / SendGrid 等：按服务商文档填 HOST/PORT/USER/PASSWORD。

**安全提醒**：不要把 `.env` 或授权码提交到 Git，也不要粘贴到聊天/文档中。若已泄露，请立即在邮箱设置里重新生成授权码并更新 `.env`。

## 三、在代码里发邮件

```python
from src.services.email_service import send_email, send_welcome_email

# 发一封自定义邮件
send_email(
    to="user@example.com",
    subject="标题",
    body_text="纯文本内容",
    body_html="<p>HTML 内容</p>",
)

# 发欢迎邮件（注册成功后已自动调用，也可手动）
send_welcome_email("user@example.com", display_name="用户名")
```

发送失败（未配置或 SMTP 报错）时返回 `False`，不会抛异常，可据此打日志或提示。

## 四、可选扩展

- **邮箱验证**：注册后发带验证链接的邮件，用户点击后标记 `email_verified`，需在 User 表增加 `email_verified` 字段和验证接口。
- **找回密码**：发带重置链接的邮件，需增加“忘记密码”接口与临时 token 存储。
- **异步发信**：高并发时可用 Celery/BackgroundTasks 在后台发邮件，避免阻塞注册接口。
