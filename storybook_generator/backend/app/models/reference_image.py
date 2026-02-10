from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ReferenceImage(Base):
    """参考图模型（阶段一生成的人物/非人物/场景）"""
    __tablename__ = "reference_images"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # 参考图信息
    ref_type = Column(String(50), nullable=False)  # character, non_character, scene
    ref_name = Column(String(255), nullable=False)  # 参考图名称
    ref_index = Column(Integer, nullable=False)  # 在同类型中的序号（如人物1、人物2）
    
    # 提示词
    prompt = Column(Text, nullable=False)  # 完整提示词
    prompt_data = Column(JSON, nullable=True)  # 结构化提示词数据
    
    # 生成的图片
    image_url = Column(String(500), nullable=True)  # 本地存储路径或URL
    image_path = Column(String(500), nullable=True)  # 本地文件路径
    
    # 生成信息
    platform = Column(String(50), nullable=True)  # 生图平台
    generation_params = Column(JSON, nullable=True)  # 生成参数
    
    # 状态
    status = Column(String(50), default="pending")  # pending, generated, confirmed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="reference_images")
