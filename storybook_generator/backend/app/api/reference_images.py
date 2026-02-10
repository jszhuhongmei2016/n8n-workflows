from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Project, ReferenceImage
from app.services import dify_service, image_service
from app.utils import save_image_from_url

router = APIRouter()


# Pydantic模型
class ReferenceImageResponse(BaseModel):
    id: int
    project_id: int
    ref_type: str
    ref_name: str
    ref_index: int
    prompt: str
    image_url: Optional[str]
    image_path: Optional[str]
    status: str
    
    class Config:
        from_attributes = True


@router.post("/projects/{project_id}/generate-prompts")
async def generate_reference_prompts(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """阶段一：生成所有参考图提示词"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.content:
        raise HTTPException(status_code=400, detail="请先上传绘本内容")
    
    if not project.style_prompt:
        raise HTTPException(status_code=400, detail="请先设置风格提示词")
    
    try:
        # 调用Dify生成提示词
        prompts_data = await dify_service.generate_stage1_prompts(
            project.content,
            project.style_prompt,
            project.target_age
        )
        
        # 保存到数据库
        saved_refs = []
        
        # 人物角色
        for idx, char in enumerate(prompts_data.get("characters", []), 1):
            ref_img = ReferenceImage(
                project_id=project_id,
                ref_type="character",
                ref_name=char["name"],
                ref_index=idx,
                prompt=char["prompt"],
                prompt_data=char
            )
            db.add(ref_img)
            saved_refs.append(ref_img)
        
        # 非人物角色
        for idx, non_char in enumerate(prompts_data.get("non_characters", []), 1):
            ref_img = ReferenceImage(
                project_id=project_id,
                ref_type="non_character",
                ref_name=non_char["name"],
                ref_index=idx,
                prompt=non_char["prompt"],
                prompt_data=non_char
            )
            db.add(ref_img)
            saved_refs.append(ref_img)
        
        # 场景
        for idx, scene in enumerate(prompts_data.get("scenes", []), 1):
            ref_img = ReferenceImage(
                project_id=project_id,
                ref_type="scene",
                ref_name=scene["name"],
                ref_index=idx,
                prompt=scene["prompt"],
                prompt_data=scene
            )
            db.add(ref_img)
            saved_refs.append(ref_img)
        
        await db.commit()
        
        # 刷新所有对象
        for ref in saved_refs:
            await db.refresh(ref)
        
        return {
            "message": "参考图提示词生成成功",
            "count": len(saved_refs),
            "references": saved_refs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/projects/{project_id}/references", response_model=List[ReferenceImageResponse])
async def list_reference_images(
    project_id: int,
    ref_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取项目的参考图列表"""
    query = select(ReferenceImage).where(ReferenceImage.project_id == project_id)
    
    if ref_type:
        query = query.where(ReferenceImage.ref_type == ref_type)
    
    query = query.order_by(ReferenceImage.ref_type, ReferenceImage.ref_index)
    
    result = await db.execute(query)
    references = result.scalars().all()
    
    return references


@router.get("/{ref_id}", response_model=ReferenceImageResponse)
async def get_reference_image(
    ref_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取参考图详情"""
    result = await db.execute(select(ReferenceImage).where(ReferenceImage.id == ref_id))
    ref_img = result.scalar_one_or_none()
    
    if not ref_img:
        raise HTTPException(status_code=404, detail="参考图不存在")
    
    return ref_img


@router.put("/{ref_id}/prompt")
async def update_reference_prompt(
    ref_id: int,
    prompt: str,
    db: AsyncSession = Depends(get_db)
):
    """更新参考图提示词"""
    result = await db.execute(select(ReferenceImage).where(ReferenceImage.id == ref_id))
    ref_img = result.scalar_one_or_none()
    
    if not ref_img:
        raise HTTPException(status_code=404, detail="参考图不存在")
    
    ref_img.prompt = prompt
    await db.commit()
    
    return {"message": "提示词更新成功"}


@router.post("/{ref_id}/generate")
async def generate_reference_image(
    ref_id: int,
    db: AsyncSession = Depends(get_db)
):
    """生成参考图（调用生图API）"""
    result = await db.execute(select(ReferenceImage).where(ReferenceImage.id == ref_id))
    ref_img = result.scalar_one_or_none()
    
    if not ref_img:
        raise HTTPException(status_code=404, detail="参考图不存在")
    
    # 获取项目配置
    result = await db.execute(select(Project).where(Project.id == ref_img.project_id))
    project = result.scalar_one_or_none()
    
    try:
        # 调用生图服务
        gen_result = await image_service.generate_image(
            prompt=ref_img.prompt,
            platform=project.platform,
            size=project.image_size,
            resolution=project.image_resolution
        )
        
        # 保存生成信息
        ref_img.generation_params = gen_result
        ref_img.status = "processing"
        ref_img.platform = project.platform
        await db.commit()
        
        return {
            "message": "图片生成已启动",
            "task_id": gen_result.get("task_id"),
            "status": gen_result.get("status")
        }
        
    except Exception as e:
        ref_img.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/{ref_id}/check-status")
async def check_generation_status(
    ref_id: int,
    db: AsyncSession = Depends(get_db)
):
    """检查生成状态并更新"""
    result = await db.execute(select(ReferenceImage).where(ReferenceImage.id == ref_id))
    ref_img = result.scalar_one_or_none()
    
    if not ref_img:
        raise HTTPException(status_code=404, detail="参考图不存在")
    
    if not ref_img.generation_params:
        raise HTTPException(status_code=400, detail="未找到生成任务")
    
    task_id = ref_img.generation_params.get("task_id")
    platform = ref_img.platform
    
    try:
        # 查询状态
        status = await image_service.check_status(task_id, platform)
        
        if status["status"] == "completed" and status.get("image_url"):
            # 下载并保存图片
            local_path = await save_image_from_url(status["image_url"], "reference_images")
            ref_img.image_url = status["image_url"]
            ref_img.image_path = local_path
            ref_img.status = "confirmed"
        elif status["status"] == "failed":
            ref_img.status = "failed"
        else:
            ref_img.status = "processing"
        
        await db.commit()
        await db.refresh(ref_img)
        
        return {
            "status": ref_img.status,
            "image_url": ref_img.image_url,
            "image_path": ref_img.image_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.delete("/{ref_id}")
async def delete_reference_image(
    ref_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除参考图"""
    result = await db.execute(select(ReferenceImage).where(ReferenceImage.id == ref_id))
    ref_img = result.scalar_one_or_none()
    
    if not ref_img:
        raise HTTPException(status_code=404, detail="参考图不存在")
    
    await db.delete(ref_img)
    await db.commit()
    
    return {"message": "参考图已删除"}
