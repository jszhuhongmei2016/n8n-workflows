from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Project, Page, ReferenceImage
from app.utils import (
    export_prompts_to_excel,
    import_prompts_from_excel,
    export_reference_images_to_excel,
    save_uploaded_file
)

router = APIRouter()


@router.get("/projects/{project_id}/prompts/excel")
async def export_project_prompts(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """导出项目的页面提示词为Excel（步骤9）"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有页面
    result = await db.execute(
        select(Page)
        .where(Page.project_id == project_id)
        .order_by(Page.page_index)
    )
    pages = result.scalars().all()
    
    if not pages:
        raise HTTPException(status_code=400, detail="没有可导出的页面")
    
    # 准备数据
    pages_data = [
        {
            "page_number": p.page_number,
            "scene_type": p.scene_type,
            "prompt": p.prompt
        }
        for p in pages
    ]
    
    try:
        # 生成Excel
        filepath = export_prompts_to_excel(pages_data, project.name)
        
        # 返回文件
        return FileResponse(
            path=filepath,
            filename=f"{project.name}_prompts.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/projects/{project_id}/prompts/import")
async def import_project_prompts(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """导入Excel更新提示词（步骤9）"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 保存上传的文件
    file_content = await file.read()
    filepath = await save_uploaded_file(file_content, file.filename, "temp")
    
    try:
        # 读取Excel
        pages_data = import_prompts_from_excel(filepath)
        
        # 更新数据库
        updated_count = 0
        for page_data in pages_data:
            result = await db.execute(
                select(Page)
                .where(Page.project_id == project_id)
                .where(Page.page_number == page_data["page_number"])
            )
            page = result.scalar_one_or_none()
            
            if page:
                page.prompt = page_data["prompt"]
                page.scene_type = page_data["scene_type"]
                updated_count += 1
        
        await db.commit()
        
        return {
            "message": f"成功更新 {updated_count} 个页面",
            "updated_count": updated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/projects/{project_id}/references/excel")
async def export_reference_prompts(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """导出参考图提示词为Excel"""
    # 获取项目
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有参考图
    result = await db.execute(
        select(ReferenceImage)
        .where(ReferenceImage.project_id == project_id)
        .order_by(ReferenceImage.ref_type, ReferenceImage.ref_index)
    )
    references = result.scalars().all()
    
    if not references:
        raise HTTPException(status_code=400, detail="没有可导出的参考图")
    
    # 准备数据
    refs_data = [
        {
            "ref_type": r.ref_type,
            "ref_name": r.ref_name,
            "prompt": r.prompt
        }
        for r in references
    ]
    
    try:
        # 生成Excel
        filepath = export_reference_images_to_excel(refs_data, project.name)
        
        # 返回文件
        return FileResponse(
            path=filepath,
            filename=f"{project.name}_reference_images.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/images/{image_id}/download")
async def download_image(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """下载单张图片"""
    from app.models import GeneratedImage
    
    result = await db.execute(
        select(GeneratedImage).where(GeneratedImage.id == image_id)
    )
    gen_img = result.scalar_one_or_none()
    
    if not gen_img:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    if not gen_img.image_path:
        raise HTTPException(status_code=400, detail="图片文件不存在")
    
    return FileResponse(
        path=gen_img.image_path,
        media_type="image/png",
        filename=f"storybook_{gen_img.id}.png"
    )


@router.post("/pages/{page_id}/download-final")
async def download_final_image(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """下载页面最终选择的图片"""
    from app.models import GeneratedImage, Page
    
    # 获取页面
    result = await db.execute(select(Page).where(Page.id == page_id))
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    # 获取最终图片
    result = await db.execute(
        select(GeneratedImage)
        .where(GeneratedImage.page_id == page_id)
        .where(GeneratedImage.is_final == True)
    )
    gen_img = result.scalar_one_or_none()
    
    if not gen_img:
        raise HTTPException(status_code=404, detail="未找到最终选择的图片")
    
    if not gen_img.image_path:
        raise HTTPException(status_code=400, detail="图片文件不存在")
    
    return FileResponse(
        path=gen_img.image_path,
        media_type="image/png",
        filename=f"{page.page_number}.png"
    )
