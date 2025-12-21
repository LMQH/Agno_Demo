"""自定义模型类，用于 Agno Agent。"""
from typing import Optional, List, Dict, Any, Union, AsyncIterator, Iterator
from agno.models.base import Model
from agno.models.response import ModelResponse
from agno.models.message import Message
import httpx
import json
import time
from ...config import get_config, LLMConfig


class CustomModel(Model):
    """自定义模型类，适配自定义 LLM API。"""
    
    def __init__(
        self,
        id: str = "deepseek-v3.2-exp",
        name: str = "CustomModel",
        provider: str = "Custom",
        config: Optional[LLMConfig] = None,
        **kwargs
    ):
        """初始化自定义模型。
        
        Args:
            id: 模型 ID
            name: 模型名称
            provider: 提供商名称
            config: LLM 配置对象
            **kwargs: 其他模型参数
        """
        if config is None:
            config = get_config().llm
        
        self.config = config
        self.api_base = config.api_base
        self.api_key = config.api_key
        self.model_id = id or config.model_name
        
        # 调用父类初始化
        super().__init__(
            id=self.model_id,
            name=name,
            provider=provider,
            **kwargs
        )
    
    def _get_headers(self) -> dict:
        """获取 API 请求头。"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _parse_provider_response(self, response: Dict[str, Any]) -> ModelResponse:
        """解析提供商响应为 ModelResponse。
        
        Args:
            response: API 响应字典
            
        Returns:
            ModelResponse 对象
        """
        # 提取响应内容
        content = None
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
        elif "content" in response:
            content = response["content"]
        elif "message" in response:
            content = response["message"].get("content", str(response))
        else:
            content = str(response)
        
        return ModelResponse(
            role="assistant",
            content=content,
            provider_data=response
        )
    
    def _parse_provider_response_delta(self, delta: Dict[str, Any]) -> str:
        """解析流式响应的增量数据。
        
        Args:
            delta: 增量响应数据
        
        Returns:
            增量内容字符串
        """
        if "choices" in delta and len(delta["choices"]) > 0:
            delta_obj = delta["choices"][0].get("delta", {})
            return delta_obj.get("content", "")
        elif "content" in delta:
            return delta["content"]
        elif "delta" in delta:
            return delta["delta"].get("content", "")
        return ""
    
    async def ainvoke(
        self,
        messages: List[Message],
        **kwargs
    ) -> ModelResponse:
        """异步调用模型（主要方法）。
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            ModelResponse 对象
        """
        return await self.aresponse(messages, **kwargs)
    
    async def ainvoke_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[ModelResponse]:
        """异步流式调用模型。
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Yields:
            ModelResponse 对象（流式）
        """
        # 如果 API 不支持流式，回退到普通调用
        response = await self.aresponse(messages, **kwargs)
        yield response
    
    def invoke(
        self,
        messages: List[Message],
        **kwargs
    ) -> ModelResponse:
        """同步调用模型。
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            ModelResponse 对象
        """
        import asyncio
        import nest_asyncio
        
        # 允许嵌套事件循环（解决在异步环境中调用同步方法的问题）
        nest_asyncio.apply()
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.ainvoke(messages, **kwargs))
    
    def invoke_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Iterator[ModelResponse]:
        """同步流式调用模型。
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
        
        Yields:
            ModelResponse 对象（流式）
        """
        import asyncio
        import nest_asyncio
        
        # 允许嵌套事件循环（解决在异步环境中调用同步方法的问题）
        nest_asyncio.apply()
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def _async_gen():
            async for item in self.ainvoke_stream(messages, **kwargs):
                yield item
        
        gen = _async_gen()
        while True:
            try:
                yield loop.run_until_complete(gen.__anext__())
            except StopAsyncIteration:
                break
    
    async def aresponse(
        self,
        messages: List[Message],
        response_format: Optional[Union[Dict, Any]] = None,
        tools: Optional[List[Any]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        tool_call_limit: Optional[int] = None,
        run_response: Optional[Any] = None,
        send_media_to_model: bool = True,
        **kwargs
    ) -> ModelResponse:
        """异步生成响应。
        
        Args:
            messages: 消息列表
            response_format: 响应格式
            tools: 工具列表
            tool_choice: 工具选择
            tool_call_limit: 工具调用限制
            run_response: 运行响应
            send_media_to_model: 是否发送媒体到模型
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            ModelResponse 对象
        """
        if not self.api_base:
            raise ValueError("LLM API base URL not configured")
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, Message):
                # 从 Message 对象提取信息
                role = getattr(msg, 'role', 'user')
                content = getattr(msg, 'content', '')
                if content:
                    formatted_messages.append({
                        "role": role,
                        "content": str(content)
                    })
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                formatted_messages.append({
                    "role": msg.role,
                    "content": str(msg.content)
                })
            else:
                # 尝试从字符串或其他格式转换
                formatted_messages.append({
                    "role": "user",
                    "content": str(msg)
                })
        
        # 构建请求负载
        payload = {
            "model": self.model_id,
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        # 发送请求
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.api_base,
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                
                # 使用 _parse_provider_response 解析响应
                return self._parse_provider_response(data)
            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to generate response: {e}")

