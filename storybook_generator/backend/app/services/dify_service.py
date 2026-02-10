import httpx
from typing import Dict, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DifyService:
    """Dify工作流集成服务"""
    
    def __init__(self):
        self.api_key = settings.DIFY_API_KEY
        self.base_url = settings.DIFY_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def run_workflow(self, workflow_id: str, inputs: Dict[str, Any], user: str = "user") -> Dict[str, Any]:
        """
        运行Dify工作流
        
        Args:
            workflow_id: 工作流ID
            inputs: 输入参数
            user: 用户标识
            
        Returns:
            工作流执行结果
        """
        url = f"{self.base_url}/workflows/run"
        
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    headers={**self.headers, "X-Workflow-Id": workflow_id},
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Dify API请求失败: {str(e)}")
            raise Exception(f"Dify工作流执行失败: {str(e)}")
    
    async def generate_stage1_prompts(
        self, 
        storybook_content: str, 
        style_prompt: str,
        target_age: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        阶段一：生成参考图提示词
        
        Args:
            storybook_content: 绘本完整内容
            style_prompt: 风格提示词
            target_age: 目标年龄段
            
        Returns:
            {
                "characters": [{"name": "xx", "prompt": "..."}],
                "non_characters": [{"name": "xx", "prompt": "..."}],
                "scenes": [{"name": "xx", "prompt": "..."}]
            }
        """
        inputs = {
            "storybook_content": storybook_content,
            "style_prompt": style_prompt,
            "target_age": target_age or "7-9岁"
        }
        
        workflow_id = settings.DIFY_WORKFLOW_STAGE1
        if not workflow_id:
            raise Exception("未配置DIFY_WORKFLOW_STAGE1")
        
        result = await self.run_workflow(workflow_id, inputs)
        return result.get("data", {}).get("outputs", {})
    
    async def generate_page_prompt(
        self,
        page_number: str,
        page_content: str,
        scene_type: str,
        style_prompt: str,
        reference_images: Dict[str, Any],
        target_age: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        阶段二：生成单页绘本提示词
        
        Args:
            page_number: 页码（如P1）
            page_content: 页面文本内容
            scene_type: 画面类型（real_scene/knowledge/abstract）
            style_prompt: 风格提示词
            reference_images: 引用的参考图信息
            target_age: 目标年龄段
            
        Returns:
            {
                "prompt": "完整提示词",
                "modules": {
                    "page_number": "...",
                    "scene_type": "...",
                    "style": "...",
                    ...
                }
            }
        """
        inputs = {
            "page_number": page_number,
            "page_content": page_content,
            "scene_type": scene_type,
            "style_prompt": style_prompt,
            "reference_images": reference_images,
            "target_age": target_age or "7-9岁"
        }
        
        workflow_id = settings.DIFY_WORKFLOW_STAGE2
        if not workflow_id:
            raise Exception("未配置DIFY_WORKFLOW_STAGE2")
        
        result = await self.run_workflow(workflow_id, inputs)
        return result.get("data", {}).get("outputs", {})
    
    async def select_best_image(
        self,
        images_data: list[Dict[str, Any]],
        page_content: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        使用Gemini选择最佳图片
        
        Args:
            images_data: 图片列表，每项包含url和其他信息
            page_content: 页面内容
            prompt: 生成提示词
            
        Returns:
            {
                "selected_index": 0,
                "scores": [85, 90, 78],
                "reasons": ["...", "...", "..."]
            }
        """
        inputs = {
            "images": images_data,
            "page_content": page_content,
            "prompt": prompt
        }
        
        workflow_id = settings.DIFY_WORKFLOW_IMAGE_SELECTOR
        if not workflow_id:
            raise Exception("未配置DIFY_WORKFLOW_IMAGE_SELECTOR")
        
        result = await self.run_workflow(workflow_id, inputs)
        return result.get("data", {}).get("outputs", {})
    
    async def reverse_prompt_from_image(
        self,
        image_url: str,
        style_description: Optional[str] = None
    ) -> str:
        """
        从参考图反推提示词
        
        Args:
            image_url: 图片URL
            style_description: 风格描述（可选）
            
        Returns:
            反推的提示词
        """
        # 这个功能可以集成到stage1工作流中，或单独创建一个工作流
        inputs = {
            "image_url": image_url,
            "style_description": style_description or ""
        }
        
        # 可以使用stage1工作流的变体
        workflow_id = settings.DIFY_WORKFLOW_STAGE1
        if not workflow_id:
            raise Exception("未配置反推提示词工作流")
        
        result = await self.run_workflow(workflow_id, inputs)
        return result.get("data", {}).get("outputs", {}).get("prompt", "")


# 创建全局实例
dify_service = DifyService()
