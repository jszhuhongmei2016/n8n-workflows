from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class GeneratedImage(Base):
    """生成的图片模型"""
    __tablename__ = "generated_images"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    
    # 图片信息
    image_url = Column(String(500), nullable=True)  # 远程URL
    image_path = Column(String(500), nullable=True)  # 本地存储路径
    thumbnail_path = Column(String(500), nullable=True)  # 缩略图路径
    
    # 生成信息
    platform = Column(String(50), nullable=False)  # jimeng, volcano, mj
    generation_params = Column(JSON, nullable=True)  # 生成参数
    task_id = Column(String(255), nullable=True)  # 生图任务ID
    
    # AI评分
    ai_score = Column(Float, nullable=True)  # Gemini评分（0-100）
    ai_reason = Column(Text, nullable=True)  # 评分理由
    is_ai_selected = Column(Boolean, default=False)  # 是否被AI选中
    
    # 用户选择
    is_user_selected = Column(Boolean, default=False)  # 是否被用户选中
    is_final = Column(Boolean, default=False)  # 是否为最终选择
    
    # 状态
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)  # 错误信息
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    page = relationship("Page", back_populates="generated_images")
