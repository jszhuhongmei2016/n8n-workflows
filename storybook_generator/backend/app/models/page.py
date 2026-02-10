from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Page(Base):
    """绘本页面模型（阶段二）"""
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # 页面信息
    page_number = Column(String(20), nullable=False)  # P1, P2, ...
    page_index = Column(Integer, nullable=False)  # 排序用
    page_content = Column(Text, nullable=False)  # 该页的文本内容
    
    # 画面类型
    scene_type = Column(String(50), nullable=False)  # real_scene, knowledge, abstract
    
    # 调用的参考图（最多6个）
    reference_character_ids = Column(JSON, nullable=True)  # 人物角色ID列表（≤3）
    reference_non_character_ids = Column(JSON, nullable=True)  # 非人物角色ID列表（≤2）
    reference_scene_id = Column(Integer, nullable=True)  # 场景ID（≤1）
    
    # 完整提示词
    prompt = Column(Text, nullable=False)  # 完整的10模块提示词
    prompt_data = Column(JSON, nullable=True)  # 结构化的提示词数据
    
    # 镜头信息
    shot_type = Column(String(50), nullable=True)  # 景别
    composition = Column(String(100), nullable=True)  # 构图
    
    # 状态
    status = Column(String(50), default="pending")  # pending, generated, selected, confirmed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="pages")
    generated_images = relationship("GeneratedImage", back_populates="page", cascade="all, delete-orphan")
