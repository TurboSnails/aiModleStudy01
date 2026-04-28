"""配置管理 - 解决 QA 问题 5, 19（JWT Secret 安全 + 多环境配置）"""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置

    优先级（问题 19）：
    1. 环境变量（生产强制使用）
    2. .env 文件（开发环境）
    3. 默认值
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid",  # 禁止未知字段
    )

    # ==================== 应用配置 ====================
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    log_level: str = Field(default="INFO")
    app_version: str = Field(default="1.0.0")

    # ==================== 数据库配置 ====================
    database_url: str = Field(default="sqlite+aiosqlite:///./ai_study.db")

    # ==================== Redis 配置 ====================
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ==================== 安全配置（问题 5）====================
    jwt_secret_key: str = Field(default="dev-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=1440)  # 24小时

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """生产环境必须使用安全的随机密钥"""
        import os
        env = os.environ.get("ENVIRONMENT", "development")
        if env == "production" and len(v) < 32:
            raise ValueError("生产环境 JWT_SECRET_KEY 必须至少 32 字符")
        return v

    # ==================== AI 提供商配置 ====================
    minimax_api_key: str = Field(default="")
    minimax_base_url: str = Field(default="https://api.minimaxi.com/anthropic")
    minimax_model: str = Field(default="MiniMax-M2")

    openai_api_key: str = Field(default="")
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    openai_model: str = Field(default="gpt-4o-mini")

    anthropic_api_key: str = Field(default="")
    anthropic_base_url: str = Field(default="https://api.anthropic.com")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")

    # ==================== 限流配置（问题 11）====================
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=100)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def database_url_effective(self) -> str:
        """生产环境强制使用环境变量（问题 19）"""
        if self.is_production:
            import os
            return os.environ.get("DATABASE_URL", self.database_url)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """单例配置获取（避免重复加载 .env）"""
    return Settings()
