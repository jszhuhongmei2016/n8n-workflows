import aiofiles
import os
from pathlib import Path
from typing import Optional
import uuid
from app.config import settings
from PIL import Image
import io


async def save_uploaded_file(file_content: bytes, filename: str, subfolder: str = "") -> str:
    """
    保存上传的文件
    
    Args:
        file_content: 文件内容
        filename: 文件名
        subfolder: 子文件夹
        
    Returns:
        保存的文件路径
    """
    # 生成唯一文件名
    ext = Path(filename).suffix
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # 构建保存路径
    save_dir = Path(settings.STORAGE_PATH) / subfolder
    save_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = save_dir / unique_filename
    
    # 异步保存文件
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)
    
    return str(file_path)


async def save_image_from_url(image_url: str, subfolder: str = "images") -> str:
    """
    从URL下载并保存图片
    
    Args:
        image_url: 图片URL
        subfolder: 子文件夹
        
    Returns:
        保存的文件路径
    """
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        response.raise_for_status()
        
        # 从URL或Content-Type推断扩展名
        ext = ".png"  # 默认
        content_type = response.headers.get("content-type", "")
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        
        image_content = response.content
    
    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # 构建保存路径
    save_dir = Path(settings.STORAGE_PATH) / subfolder
    save_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = save_dir / unique_filename
    
    # 保存图片
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(image_content)
    
    return str(file_path)


async def create_thumbnail(image_path: str, max_size: tuple = (400, 400)) -> str:
    """
    创建缩略图
    
    Args:
        image_path: 原图路径
        max_size: 最大尺寸
        
    Returns:
        缩略图路径
    """
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # 生成缩略图路径
    path = Path(image_path)
    thumbnail_path = path.parent / f"{path.stem}_thumb{path.suffix}"
    
    # 保存缩略图
    img.save(thumbnail_path, optimize=True, quality=85)
    
    return str(thumbnail_path)


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.allowed_extensions_list


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    return os.path.getsize(file_path)


async def delete_file(file_path: str) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否删除成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"删除文件失败: {str(e)}")
        return False


def parse_storybook_content(content: str) -> list[dict]:
    """
    解析绘本内容（P1、P2格式）
    
    Args:
        content: 绘本文本内容
        
    Returns:
        [{"page_number": "P1", "content": "..."}, ...]
    """
    pages = []
    lines = content.strip().split('\n')
    
    current_page = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检查是否是页码标记
        if line.startswith('P') and len(line) <= 4:
            # 保存上一页
            if current_page:
                pages.append({
                    "page_number": current_page,
                    "page_index": len(pages) + 1,
                    "content": '\n'.join(current_content).strip()
                })
            
            # 开始新页
            current_page = line
            current_content = []
        else:
            current_content.append(line)
    
    # 保存最后一页
    if current_page:
        pages.append({
            "page_number": current_page,
            "page_index": len(pages) + 1,
            "content": '\n'.join(current_content).strip()
        })
    
    return pages
