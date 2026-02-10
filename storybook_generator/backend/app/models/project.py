from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 配置信息
    target_age = Column(String(50), nullable=True)  # 目标年龄段
    image_size = Column(String(50), default="16:9")  # 图像尺寸
    image_resolution = Column(String(50), default="2K")  # 图像分辨率
    platform = Column(String(50), default="jimeng")  # 生图平台
    
    # 风格配置
    style_name = Column(String(100), nullable=True)  # 风格名称
    style_prompt = Column(Text, nullable=True)  # 风格提示词
    style_reference_url = Column(String(500), nullable=True)  # 风格参考图URL
    
    # 绘本内容
    content = Column(Text, nullable=True)  # 绘本文本内容（P1、P2...）
    
    # 状态信息
    status = Column(String(50), default="created")  # created, stage1_done, stage2_done, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    reference_images = relationship("ReferenceImage", back_populates="project", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan")
