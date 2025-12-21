"""LLM 基础接口定义。"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseLLM(ABC):
    """LLM 基础接口。"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """生成文本响应。"""
        pass

