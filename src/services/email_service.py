"""
基于 SMTP 的邮件发送。配置 SMTP_* 后即可在注册等场景发送邮件。
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from src.config import get_settings


def _is_configured() -> bool:
    s = get_settings().email
    return bool(s.smtp_host and s.smtp_user and s.smtp_password)


def send_email(
    to: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> bool:
    """
    发送一封邮件。若未配置 SMTP 或发送失败返回 False，成功返回 True。
    """
    if not _is_configured():
        return False
    s = get_settings().email
    from_addr = s.from_email or s.smtp_user
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    try:
        if s.use_tls and s.smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=context) as server:
                server.login(s.smtp_user, s.smtp_password)
                server.sendmail(from_addr, [to], msg.as_string())
        else:
            with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
                if s.use_tls:
                    server.starttls()
                server.login(s.smtp_user, s.smtp_password)
                server.sendmail(from_addr, [to], msg.as_string())
        return True
    except Exception:
        return False


def send_welcome_email(to: str, display_name: Optional[str] = None) -> bool:
    """注册成功后发送欢迎邮件。"""
    name = display_name or to.split("@")[0]
    subject = "欢迎使用 AI 内容永动机"
    body_text = f"""你好 {name}，

感谢注册。你可以登录后使用「拆解 → 想清楚 → 写一次 → 用到极致」四步内容工作流。

如需更多使用次数，请联系管理员充值。
"""
    body_html = f"""
<p>你好 {name}，</p>
<p>感谢注册。你可以登录后使用「拆解 → 想清楚 → 写一次 → 用到极致」四步内容工作流。</p>
<p>如需更多使用次数，请联系管理员充值。</p>
"""
    return send_email(to, subject, body_text, body_html)
