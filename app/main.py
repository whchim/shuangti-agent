"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api import auth, user, chat, knowledge, search, model, memory, tools, health

# 配置 Loguru
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="INFO",
    encoding="utf-8",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("正在启动双体智能体系统...")
    await init_db()
    logger.info("数据库初始化完成")
    yield
    await close_db()
    logger.info("应用已关闭")


app = FastAPI(
    title="双体智能体系统 API",
    description="双体软件精英产业学院智能对话系统后端",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(search.router)
app.include_router(model.router)
app.include_router(memory.router)
app.include_router(tools.router)
app.include_router(health.router)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误", "detail": str(exc) if settings.debug else "请稍后重试"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
