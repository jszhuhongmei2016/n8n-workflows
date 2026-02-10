from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "Storybook Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./storybook.db"
    
    # Dify配置
    DIFY_API_KEY: str = ""
    DIFY_BASE_URL: str = "https://api.dify.ai/v1"
    DIFY_WORKFLOW_STAGE1: str = ""
    DIFY_WORKFLOW_STAGE2: str = ""
    DIFY_WORKFLOW_IMAGE_SELECTOR: str = ""
    
    # 生图API配置
    JIMENG_API_KEY: str = ""
    JIMENG_BASE_URL: str = "https://api.jimeng.com"
    VOLCANO_API_KEY: str = ""
    VOLCANO_BASE_URL: str = "https://api.volcengine.com"
    MJ_API_KEY: str = ""
    MJ_BASE_URL: str = "https://api.midjourney.com"
    
    # 文件存储配置
    STORAGE_PATH: str = "./storage"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "txt,json"
    
    # CORS配置
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
