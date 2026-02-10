from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.api import projects, reference_images, pages, images, exports

# 配置日志
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("初始化数据库...")
    await init_db()
    logger.info("应用启动完成")
    
    yield
    
    # 关闭时
    logger.info("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="动态绘本自动生成图片系统",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/storage", StaticFiles(directory=settings.STORAGE_PATH), name="storage")

# 注册路由
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(reference_images.router, prefix="/api/reference-images", tags=["Reference Images"])
app.include_router(pages.router, prefix="/api/pages", tags=["Pages"])
app.include_router(images.router, prefix="/api/images", tags=["Images"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
