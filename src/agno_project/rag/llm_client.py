"""用于自定义模型推理的 LLM 客户端。"""
from typing import List, Dict, Any, Optional
import httpx
import json
from ..config import get_config, LLMConfig


class LLMClient:
    """自定义 LLM API 客户端（deepseek-v3.2-exp）。"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """初始化 LLM 客户端。"""
        if config is None:
            config = get_config().llm
        
        self.config = config
        self.api_base = config.api_base
        self.api_key = config.api_key
        self.model_name = config.model_name
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
    
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

