from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.models import Project, Page, ReferenceImage
from app.services import dify_service
from app.utils import parse_storybook_content

router = APIRouter()


# Pydantic模型
class PagePlanningRequest(BaseModel):
    page_number: str
    scene_type: str  # real_scene, knowledge, abstract
    character_ids: List[int] = []  # 最多3个
    non_character_ids: List[int] = []  # 最多2个
    scene_id: Optional[int] = None  # 最多1个


class PageResponse(BaseModel):
    id: int
    project_id: int
    page_number: str
    page_index: int
    page_content: str
    scene_type: str
    prompt: str
    status: str
    
    class Config:
        from_attributes = True


@router.post("/projects/{project_id}/plan-pages")
async def plan_pages(
    project_id: int,
    pages_plan: List[PagePlanningRequest],
    db: AsyncSession = Depends(get_db)
):
    """规划绘本页面（步骤8）"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.content:
        raise HTTPException(status_code=400, detail="请先上传绘本内容")
    
    # 解析绘本内容
    pages_content = parse_storybook_content(project.content)
    content_map = {p["page_number"]: p["content"] for p in pages_content}
    
    # 创建页面记录
    saved_pages = []
    for idx, plan in enumerate(pages_plan, 1):
        # 验证参考图数量
        if len(plan.character_ids) > 3:
            raise HTTPException(status_code=400, detail=f"{plan.page_number}: 人物角色不能超过3个")
        if len(plan.non_character_ids) > 2:
            raise HTTPException(status_code=400, detail=f"{plan.page_number}: 非人物角色不能超过2个")
        
        page = Page(
            project_id=project_id,
            page_number=plan.page_number,
            page_index=idx,
            page_content=content_map.get(plan.page_number, ""),
            scene_type=plan.scene_type,
            reference_character_ids=plan.character_ids,
            reference_non_character_ids=plan.non_character_ids,
            reference_scene_id=plan.scene_id,
            prompt="",  # 待生成
            status="pending"
        )
        db.add(page)
        saved_pages.append(page)
    
    await db.commit()
    
    # 刷新对象
    for page in saved_pages:
        await db.refresh(page)
    
    return {
        "message": "页面规划完成",
        "count": len(saved_pages),
        "pages": saved_pages
    }


@router.get("/projects/{project_id}/pages", response_model=List[PageResponse])
async def list_pages(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取项目的页面列表"""
    result = await db.execute(
        select(Page)
        .where(Page.project_id == project_id)
        .order_by(Page.page_index)
    )
    pages = result.scalars().all()
    return pages


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取页面详情"""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    return page


@router.post("/{page_id}/generate-prompt")
async def generate_page_prompt(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """生成单页提示词（步骤9）"""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == page.project_id))
    project = result.scalar_one_or_none()
    
    # 收集参考图信息
    reference_images_data = {}
    
    # 查询人物角色
    if page.reference_character_ids:
        result = await db.execute(
            select(ReferenceImage)
            .where(ReferenceImage.id.in_(page.reference_character_ids))
        )
        characters = result.scalars().all()
        reference_images_data["characters"] = [
            {"name": c.ref_name, "prompt": c.prompt} for c in characters
        ]
    
    # 查询非人物角色
    if page.reference_non_character_ids:
        result = await db.execute(
            select(ReferenceImage)
            .where(ReferenceImage.id.in_(page.reference_non_character_ids))
        )
        non_characters = result.scalars().all()
        reference_images_data["non_characters"] = [
            {"name": nc.ref_name, "prompt": nc.prompt} for nc in non_characters
        ]
    
    # 查询场景
    if page.reference_scene_id:
        result = await db.execute(
            select(ReferenceImage)
            .where(ReferenceImage.id == page.reference_scene_id)
        )
        scene = result.scalar_one_or_none()
        if scene:
            reference_images_data["scene"] = {
                "name": scene.ref_name,
                "prompt": scene.prompt
            }
    
    try:
        # 调用Dify生成提示词
        prompt_data = await dify_service.generate_page_prompt(
            page_number=page.page_number,
            page_content=page.page_content,
            scene_type=page.scene_type,
            style_prompt=project.style_prompt,
            reference_images=reference_images_data,
            target_age=project.target_age
        )
        
        # 保存提示词
        page.prompt = prompt_data.get("prompt", "")
        page.prompt_data = prompt_data.get("modules", {})
        page.shot_type = prompt_data.get("modules", {}).get("shot_type", "")
        page.composition = prompt_data.get("modules", {}).get("composition", "")
        page.status = "prompt_generated"
        
        await db.commit()
        await db.refresh(page)
        
        return {
            "message": "提示词生成成功",
            "prompt": page.prompt,
            "prompt_data": page.prompt_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/projects/{project_id}/generate-all-prompts")
async def generate_all_page_prompts(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """批量生成所有页面提示词"""
    # 获取所有页面
    result = await db.execute(
        select(Page)
        .where(Page.project_id == project_id)
        .order_by(Page.page_index)
    )
    pages = result.scalars().all()
    
    if not pages:
        raise HTTPException(status_code=400, detail="未找到页面，请先规划页面")
    
    success_count = 0
    errors = []
    
    for page in pages:
        try:
            await generate_page_prompt(page.id, db)
            success_count += 1
        except Exception as e:
            errors.append(f"{page.page_number}: {str(e)}")
    
    return {
        "message": f"完成 {success_count}/{len(pages)} 个页面",
        "success_count": success_count,
        "total_count": len(pages),
        "errors": errors
    }


@router.put("/{page_id}/prompt")
async def update_page_prompt(
    page_id: int,
    prompt: str,
    db: AsyncSession = Depends(get_db)
):
    """更新页面提示词"""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    page.prompt = prompt
    await db.commit()
    
    return {"message": "提示词更新成功"}


@router.delete("/{page_id}")
async def delete_page(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除页面"""
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    await db.delete(page)
    await db.commit()
    
    return {"message": "页面已删除"}
