import httpx
from typing import Dict, Any, Optional
from app.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """图像生成服务（集成多个平台）"""
    
    def __init__(self):
        self.platform_configs = {
            "jimeng": {
                "api_key": settings.JIMENG_API_KEY,
                "base_url": settings.JIMENG_BASE_URL
            },
            "volcano": {
                "api_key": settings.VOLCANO_API_KEY,
                "base_url": settings.VOLCANO_BASE_URL
            },
            "mj": {
                "api_key": settings.MJ_API_KEY,
                "base_url": settings.MJ_BASE_URL
            }
        }
    
    async def generate_image(
        self,
        prompt: str,
        platform: str = "jimeng",
        size: str = "16:9",
        resolution: str = "2K",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图片（统一接口）
        
        Args:
            prompt: 提示词
            platform: 平台名称（jimeng/volcano/mj）
            size: 图片比例
            resolution: 分辨率
            **kwargs: 其他平台特定参数
            
        Returns:
            {
                "task_id": "...",
                "status": "pending",
                "image_url": None  # 生成完成后会有
            }
        """
        if platform == "jimeng":
            return await self._generate_jimeng(prompt, size, resolution, **kwargs)
        elif platform == "volcano":
            return await self._generate_volcano(prompt, size, resolution, **kwargs)
        elif platform == "mj":
            return await self._generate_mj(prompt, size, resolution, **kwargs)
        else:
            raise ValueError(f"不支持的平台: {platform}")
    
    async def _generate_jimeng(
        self,
        prompt: str,
        size: str,
        resolution: str,
        **kwargs
    ) -> Dict[str, Any]:
        """即梦平台生图"""
        config = self.platform_configs["jimeng"]
        
        # 转换尺寸参数
        size_map = {
            "16:9": "1920x1080",
            "9:16": "1080x1920",
            "1:1": "1024x1024",
            "4:3": "1024x768"
        }
        
        payload = {
            "prompt": prompt,
            "size": size_map.get(size, "1920x1080"),
            "quality": resolution.lower(),
            **kwargs
        }
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 注意：这里的API端点需要根据实际的即梦API文档调整
                response = await client.post(
                    f"{config['base_url']}/v1/images/generate",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "task_id": result.get("task_id") or result.get("id"),
                    "status": "pending",
                    "image_url": result.get("image_url"),
                    "platform": "jimeng"
                }
        except httpx.HTTPError as e:
            logger.error(f"即梦API请求失败: {str(e)}")
            raise Exception(f"图片生成失败: {str(e)}")
    
    async def _generate_volcano(
        self,
        prompt: str,
        size: str,
        resolution: str,
        **kwargs
    ) -> Dict[str, Any]:
        """火山引擎生图（豆包模型）"""
        config = self.platform_configs["volcano"]
        
        # 转换尺寸参数
        size_map = {
            "16:9": "1920x1080",
            "9:16": "1080x1920",
            "1:1": "1024x1024",
            "4:3": "1024x768"
        }
        
        payload = {
            "model": "doubao-seedream-4-0-250828",  # 豆包生图模型
            "prompt": prompt,
            "size": resolution,  # "2K", "4K" 等
            "response_format": "url",
            "sequential_image_generation": "disabled",
            "stream": False,
            "watermark": True,
            **kwargs
        }
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{config['base_url']}/api/v3/images/generations",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # 火山引擎返回格式：{"data": [{"url": "..."}], "request_id": "..."}
                image_url = None
                if result.get("data") and len(result["data"]) > 0:
                    image_url = result["data"][0].get("url")
                
                return {
                    "task_id": result.get("request_id"),
                    "status": "completed" if image_url else "pending",
                    "image_url": image_url,
                    "platform": "volcano"
                }
        except httpx.HTTPError as e:
            logger.error(f"火山引擎API请求失败: {str(e)}")
            raise Exception(f"图片生成失败: {str(e)}")
    
    async def _generate_mj(
        self,
        prompt: str,
        size: str,
        resolution: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Midjourney生图"""
        config = self.platform_configs["mj"]
        
        # MJ的提示词需要添加比例参数
        full_prompt = f"{prompt} --ar {size.replace(':', ' ')}"
        
        payload = {
            "prompt": full_prompt,
            **kwargs
        }
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{config['base_url']}/v1/imagine",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "task_id": result.get("task_id") or result.get("id"),
                    "status": "pending",
                    "image_url": None,
                    "platform": "mj"
                }
        except httpx.HTTPError as e:
            logger.error(f"Midjourney API请求失败: {str(e)}")
            raise Exception(f"图片生成失败: {str(e)}")
    
    async def check_status(self, task_id: str, platform: str) -> Dict[str, Any]:
        """
        检查图片生成状态
        
        Args:
            task_id: 任务ID
            platform: 平台名称
            
        Returns:
            {
                "status": "pending/processing/completed/failed",
                "image_url": "...",
                "error": "..."
            }
        """
        if platform == "jimeng":
            return await self._check_jimeng_status(task_id)
        elif platform == "volcano":
            return await self._check_volcano_status(task_id)
        elif platform == "mj":
            return await self._check_mj_status(task_id)
        else:
            raise ValueError(f"不支持的平台: {platform}")
    
    async def _check_jimeng_status(self, task_id: str) -> Dict[str, Any]:
        """检查即梦任务状态"""
        config = self.platform_configs["jimeng"]
        headers = {
            "Authorization": f"Bearer {config['api_key']}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                respo（豆包通常是同步返回，此方法用于兼容）"""
        # 火山引擎的豆包模型通常是同步返回结果，不需要轮询
        # 如果已经在生成时获得了图片URL，状态就是completed
        return {
            "status": "completed",
            "image_url": None,
            "error": None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{config['base_url']}/v1/image/query/{task_id}",
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "status": result.get("status", "pending"),
                    "image_url": result.get("url"),
                    "error": result.get("error_message")
                }
        except httpx.HTTPError as e:
            logger.error(f"查询火山引擎任务状态失败: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def _check_mj_status(self, task_id: str) -> Dict[str, Any]:
        """检查Midjourney任务状态"""
        config = self.platform_configs["mj"]
        headers = {
            "Authorization": f"Bearer {config['api_key']}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{config['base_url']}/v1/task/{task_id}",
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                # MJ的状态映射
                status_map = {
                    "pending": "pending",
                    "processing": "processing",
                    "success": "completed",
                    "failed": "failed"
                }
                
                return {
                    "status": status_map.get(result.get("status"), "pending"),
                    "image_url": result.get("image_url"),
                    "error": result.get("error")
                }
        except httpx.HTTPError as e:
            logger.error(f"查询Midjourney任务状态失败: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def wait_for_completion(
        self,
        task_id: str,
        platform: str,
        max_wait: int = 300,
        check_interval: int = 5
    ) -> Dict[str, Any]:
        """
        等待图片生成完成
        
        Args:
            task_id: 任务ID
            platform: 平台名称
            max_wait: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
            
        Returns:
            最终状态
        """
        elapsed = 0
        while elapsed < max_wait:
            status = await self.check_status(task_id, platform)
            
            if status["status"] in ["completed", "failed"]:
                return status
            
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        
        return {
            "status": "timeout",
            "error": f"等待超时（{max_wait}秒）"
        }


# 创建全局实例
image_service = ImageGenerationService()
