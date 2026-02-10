from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Page, GeneratedImage, Project
from app.services import dify_service, image_service
from app.utils import save_image_from_url, create_thumbnail

router = APIRouter()


# Pydantic模型
class GeneratedImageResponse(BaseModel):
    id: int
    page_id: int
    image_url: Optional[str]
    image_path: Optional[str]
    thumbnail_path: Optional[str]
    platform: str
    ai_score: Optional[float]
    ai_reason: Optional[str]
    is_ai_selected: bool
    is_user_selected: bool
    is_final: bool
    status: str
    
    class Config:
        from_attributes = True


@router.post("/pages/{page_id}/generate")
async def generate_page_image(
    page_id: int,
    count: int = 3,  # 生成数量
    db: AsyncSession = Depends(get_db)
):
    """生成页面图片（步骤10）"""
    # 获取页面
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    if not page.prompt:
        raise HTTPException(status_code=400, detail="请先生成提示词")
    
    # 获取项目配置
    result = await db.execute(select(Project).where(Project.id == page.project_id))
    project = result.scalar_one_or_none()
    
    # 批量生成图片
    generated_images = []
    for i in range(count):
        try:
            # 调用生图服务
            gen_result = await image_service.generate_image(
                prompt=page.prompt,
                platform=project.platform,
                size=project.image_size,
                resolution=project.image_resolution
            )
            
            # 创建记录
            gen_img = GeneratedImage(
                page_id=page_id,
                platform=project.platform,
                generation_params=gen_result,
                task_id=gen_result.get("task_id"),
                status="processing"
            )
            db.add(gen_img)
            generated_images.append(gen_img)
            
        except Exception as e:
            # 记录失败
            gen_img = GeneratedImage(
                page_id=page_id,
                platform=project.platform,
                status="failed",
                error_message=str(e)
            )
            db.add(gen_img)
    
    await db.commit()
    
    # 刷新对象
    for img in generated_images:
        await db.refresh(img)
    
    return {
        "message": f"已提交 {len(generated_images)} 个生成任务",
        "images": generated_images
    }


@router.post("/{image_id}/check-status")
async def check_image_status(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """检查图片生成状态"""
    result = await db.execute(select(GeneratedImage).where(GeneratedImage.id == image_id))
    gen_img = result.scalar_one_or_none()
    
    if not gen_img:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    if not gen_img.task_id:
        raise HTTPException(status_code=400, detail="未找到生成任务")
    
    try:
        # 查询状态
        status = await image_service.check_status(gen_img.task_id, gen_img.platform)
        
        if status["status"] == "completed" and status.get("image_url"):
            # 下载并保存图片
            local_path = await save_image_from_url(status["image_url"], "generated_images")
            
            # 创建缩略图
            thumbnail_path = await create_thumbnail(local_path)
            
            gen_img.image_url = status["image_url"]
            gen_img.image_path = local_path
            gen_img.thumbnail_path = thumbnail_path
            gen_img.status = "completed"
            
        elif status["status"] == "failed":
            gen_img.status = "failed"
            gen_img.error_message = status.get("error", "生成失败")
        else:
            gen_img.status = "processing"
        
        await db.commit()
        await db.refresh(gen_img)
        
        return {
            "status": gen_img.status,
            "image_url": gen_img.image_url,
            "thumbnail_path": gen_img.thumbnail_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/pages/{page_id}/auto-select")
async def auto_select_best_image(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """AI自动选择最佳图片（步骤11）"""
    # 获取页面
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    # 获取所有已完成的图片
    result = await db.execute(
        select(GeneratedImage)
        .where(GeneratedImage.page_id == page_id)
        .where(GeneratedImage.status == "completed")
    )
    images = result.scalars().all()
    
    if not images:
        raise HTTPException(status_code=400, detail="没有可选择的图片")
    
    # 准备图片数据
    images_data = [
        {
            "id": img.id,
            "url": img.image_url or img.image_path
        }
        for img in images
    ]
    
    try:
        # 调用Dify/Gemini选择
        selection = await dify_service.select_best_image(
            images_data,
            page.page_content,
            page.prompt
        )
        
        selected_index = selection.get("selected_index", 0)
        scores = selection.get("scores", [])
        reasons = selection.get("reasons", [])
        
        # 更新所有图片的AI评分
        for idx, img in enumerate(images):
            if idx < len(scores):
                img.ai_score = scores[idx]
            if idx < len(reasons):
                img.ai_reason = reasons[idx]
            img.is_ai_selected = (idx == selected_index)
        
        await db.commit()
        
        return {
            "message": "AI选择完成",
            "selected_image_id": images[selected_index].id,
            "scores": scores,
            "reasons": reasons
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"选择失败: {str(e)}")


@router.post("/{image_id}/select")
async def user_select_image(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """用户选择图片"""
    result = await db.execute(select(GeneratedImage).where(GeneratedImage.id == image_id))
    gen_img = result.scalar_one_or_none()
    
    if not gen_img:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 取消同页面其他图片的选择
    result = await db.execute(
        select(GeneratedImage)
        .where(GeneratedImage.page_id == gen_img.page_id)
    )
    all_images = result.scalars().all()
    
    for img in all_images:
        img.is_user_selected = (img.id == image_id)
        img.is_final = (img.id == image_id)
    
    await db.commit()
    
    return {"message": "选择成功"}


@router.get("/pages/{page_id}/images", response_model=List[GeneratedImageResponse])
async def list_page_images(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取页面的所有生成图片"""
    result = await db.execute(
        select(GeneratedImage)
        .where(GeneratedImage.page_id == page_id)
        .order_by(GeneratedImage.created_at)
    )
    images = result.scalars().all()
    return images


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除图片"""
    result = await db.execute(select(GeneratedImage).where(GeneratedImage.id == image_id))
    gen_img = result.scalar_one_or_none()
    
    if not gen_img:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    await db.delete(gen_img)
    await db.commit()
    
    return {"message": "图片已删除"}
