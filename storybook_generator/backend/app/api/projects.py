from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Project
from app.services import dify_service
from app.utils import save_uploaded_file, parse_storybook_content

router = APIRouter()


# Pydantic模型
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_age: Optional[str] = "7-9岁"
    image_size: str = "16:9"
    image_resolution: str = "2K"
    platform: str = "jimeng"
    style_name: Optional[str] = None
    style_prompt: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_age: Optional[str] = None
    image_size: Optional[str] = None
    image_resolution: Optional[str] = None
    platform: Optional[str] = None
    style_name: Optional[str] = None
    style_prompt: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_age: Optional[str]
    image_size: str
    image_resolution: str
    platform: str
    style_name: Optional[str]
    style_prompt: Optional[str]
    style_reference_url: Optional[str]
    content: Optional[str]
    status: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新项目"""
    project = Project(**project_data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取项目列表"""
    result = await db.execute(
        select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取项目详情"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新项目"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 更新字段
    for key, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除项目"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "项目已删除"}


@router.post("/{project_id}/upload-content")
async def upload_content(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传绘本文本内容"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 读取文件内容
    content = await file.read()
    text_content = content.decode('utf-8')
    
    # 解析绘本内容
    pages = parse_storybook_content(text_content)
    
    # 保存到项目
    project.content = text_content
    await db.commit()
    
    return {
        "message": "内容上传成功",
        "pages_count": len(pages),
        "pages": pages
    }


@router.post("/{project_id}/upload-style-reference")
async def upload_style_reference(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传风格参考图"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 保存文件
    file_content = await file.read()
    file_path = await save_uploaded_file(file_content, file.filename, "style_references")
    
    # 更新项目
    project.style_reference_url = file_path
    await db.commit()
    
    return {
        "message": "风格参考图上传成功",
        "file_path": file_path
    }


@router.post("/{project_id}/reverse-style-prompt")
async def reverse_style_prompt(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """从参考图反推风格提示词"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.style_reference_url:
        raise HTTPException(status_code=400, detail="未上传风格参考图")
    
    try:
        # 调用Dify反推提示词
        prompt = await dify_service.reverse_prompt_from_image(
            project.style_reference_url,
            project.style_name
        )
        
        # 保存到项目
        project.style_prompt = prompt
        await db.commit()
        
        return {
            "message": "风格提示词反推成功",
            "style_prompt": prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反推失败: {str(e)}")
