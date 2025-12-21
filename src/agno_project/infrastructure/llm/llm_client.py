"""LLM 客户端实现。"""
from typing import Optional
import httpx
from ..database.base import BaseDatabase
from ...config import get_config, LLMConfig


class LLMClient:
    """自定义 LLM API 客户端（deepseek-v3.2-exp）。"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """初始化 LLM 客户端。
        
        Args:
            config: LLM 配置对象，如果为 None 则使用默认配置
        """
        self.config = config or get_config().llm
        self.api_base = self.config.api_base
        self.api_key = self.config.api_key
        self.model_name = self.config.model_name
        self.temperature = self.config.temperature
        self.max_tokens = self.config.max_tokens
    
    def _get_headers(self) -> dict:
        """获取 API 请求头。"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用 LLM 生成文本。"""
        if not self.api_base:
            raise ValueError("LLM API base URL not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.api_base,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                
                # 提取响应内容（根据 API 响应格式适配）
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                elif "content" in data:
                    return data["content"]
                else:
                    return str(data)
            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to generate response: {e}")

