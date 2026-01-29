from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")


class AppSettings(BaseModel):
    env: str = Field(default="dev")
    port: int = Field(default=8000)
    public_base_url: str = Field(default="http://localhost:8000")


class DashScopeSettings(BaseModel):
    api_key: str = Field(default="", description="DASHSCOPE_API_KEY")
    asr_model: str = Field(default="paraformer-v1")
    llm_model: str = Field(default="qwen-plus")


class OSSSettings(BaseModel):
    endpoint: str = Field(default="oss-cn-beijing.aliyuncs.com")
    bucket: str = Field(default="sofewaccampany")
    access_key_id: str = Field(default="")
    access_key_secret: str = Field(default="")
    cname: Optional[str] = None
    use_https: bool = Field(default=True)
    prefix: str = Field(default="recordings/")


class AuthSettings(BaseModel):
    jwt_secret: str = Field(default="change-me-in-production", description="JWT 签名密钥")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_hours: int = Field(default=168, description="token 有效小时数，默认 7 天")
    admin_username: str = Field(default="YANGRONG", description="管理员账号")
    admin_password: str = Field(default="YANGRONG", description="管理员密码")
    guest_free_quota: int = Field(default=3, description="游客免费次数")


class EmailSettings(BaseModel):
    """SMTP 邮件配置。留空则不发邮件。"""
    smtp_host: str = Field(default="", description="SMTP 服务器，如 smtp.qq.com")
    smtp_port: int = Field(default=465, description="端口，465 为 SSL")
    smtp_user: str = Field(default="", description="发件邮箱账号")
    smtp_password: str = Field(default="", description="发件邮箱密码或授权码")
    from_email: str = Field(default="", description="发件人显示邮箱，默认同 smtp_user")
    use_tls: bool = Field(default=True, description="是否使用 SSL/TLS")
    send_welcome_email: bool = Field(default=False, description="注册成功后是否发欢迎邮件")


class Settings(BaseModel):
    app: AppSettings
    dashscope: DashScopeSettings
    oss: OSSSettings
    auth: AuthSettings
    email: EmailSettings


@lru_cache()
def get_settings() -> Settings:
    return Settings(
        app=AppSettings(
            env=os.getenv("ENV", "dev"),
            port=int(os.getenv("PORT", "8000")),
            public_base_url=os.getenv("PUBLIC_BASE_URL", "http://localhost:8000"),
        ),
        dashscope=DashScopeSettings(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            asr_model=os.getenv("DASHSCOPE_ASR_MODEL", "paraformer-v1"),
            llm_model=os.getenv("DASHSCOPE_LLM_MODEL", "qwen-plus"),
        ),
        oss=OSSSettings(
            endpoint=os.getenv("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com"),
            bucket=os.getenv("OSS_BUCKET", "sofewaccampany"),
            access_key_id=os.getenv("OSS_ACCESS_KEY_ID", ""),
            access_key_secret=os.getenv("OSS_ACCESS_KEY_SECRET", ""),
            cname=os.getenv("OSS_CNAME") or None,
            use_https=os.getenv("OSS_USE_HTTPS", "true").lower() == "true",
            prefix=os.getenv("OSS_PREFIX", "recordings/"),
        ),
        auth=AuthSettings(
            jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expire_hours=int(os.getenv("JWT_EXPIRE_HOURS", "168")),
            admin_username=os.getenv("ADMIN_USERNAME", "YANGRONG"),
            admin_password=os.getenv("ADMIN_PASSWORD", "YANGRONG"),
            guest_free_quota=int(os.getenv("GUEST_FREE_QUOTA", "3")),
        ),
        email=EmailSettings(
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "465")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", "")),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            send_welcome_email=os.getenv("SMTP_SEND_WELCOME_EMAIL", "false").lower() == "true",
        ),
    )


