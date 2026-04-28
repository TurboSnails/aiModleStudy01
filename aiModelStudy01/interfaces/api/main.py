"""FastAPI 主入口 - 解决 QA 问题 20（健康检查）"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aiModelStudy01.adapters import close_all_providers
from aiModelStudy01.core.models import HealthResponse
from aiModelStudy01.infrastructure import close_db, get_settings, init_db
from aiModelStudy01.infrastructure.cache.redis_client import close_redis, health_check_redis
from aiModelStudy01.infrastructure.database import health_check_db
from aiModelStudy01.interfaces.api.routers import auth, chat, session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 启动/关闭"""
    # 启动
    await init_db()
    yield
    # 关闭
    await close_all_providers()
    await close_redis()
    await close_db()


def create_app() -> FastAPI:
    """创建 FastAPI 应用（问题 22：统一 OpenAPI 文档）"""
    settings = get_settings()

    app = FastAPI(
        title="AI Model Gateway",
        description="统一的 AI 模型调用网关，支持 MiniMax / OpenAI / Anthropic 多模型接入",
        version=settings.app_version,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应配置具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(session.router, prefix="/api/v1")

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        from aiModelStudy01.core.exceptions import AppException
        if isinstance(exc, AppException):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict(),
            )
        # 未预期的异常
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误",
                    "details": {},
                    "request_id": None,
                }
            },
        )

    return app


app = create_app()


@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "message": "AI Model Gateway",
        "version": get_settings().app_version,
        "docs": "/docs",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="健康检查（问题 20）",
)
async def health_check():
    """Liveness Probe - 检查服务是否存活

    问题 20：K8s/负载均衡需要此端点
    """
    db_healthy = await health_check_db()
    redis_healthy = await health_check_redis()

    return HealthResponse(
        status="healthy" if db_healthy and redis_healthy else "degraded",
        version=get_settings().app_version,
        database="ok" if db_healthy else "error",
        redis="ok" if redis_healthy else "error",
    )


@app.get(
    "/ready",
    tags=["Health"],
    summary="就绪检查（问题 20）",
)
async def readiness_check():
    """Readiness Probe - 检查服务是否就绪

    检查所有依赖（DB、Redis、AI Provider）是否可用
    """
    from aiModelStudy01.adapters import get_provider_manager

    # 检查数据库
    if not await health_check_db():
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database unavailable"},
        )

    # 检查 Redis
    if not await health_check_redis():
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "redis unavailable"},
        )

    # 检查 AI Provider
    provider_manager = get_provider_manager()
    available = await provider_manager.get_available_providers()

    if not available:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "reason": "no AI provider available"},
        )

    return {
        "status": "ready",
        "available_providers": available,
    }


# 创建应用实例
app = create_app()
