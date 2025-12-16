"""使用 OpenAI text-embedding 模型生成嵌入向量。"""
from typing import List, Optional
import httpx
import asyncio
from ..config import get_config, EmbeddingConfig


class EmbeddingGenerator:
    """使用 OpenAI 兼容 API 为文本生成嵌入向量。"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """初始化嵌入向量生成器。"""
        if config is None:
            config = get_config().embedding
        
        self.config = config
        self.api_base = config.api_base or "https://api.openai.com/v1"
        self.api_key = config.api_key
        self.model_name = config.model_name
        self.dimension = config.dimension
        
        # 复用httpx客户端，避免频繁创建连接
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """获取或创建httpx客户端（复用连接）。"""
        if self._client is None:
            # 使用连接池，限制并发连接数
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=limits
            )
        return self._client
    
    async def close(self):
        """关闭客户端连接。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    def _get_headers(self) -> dict:
        """获取 API 请求头。"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """为文本列表生成嵌入向量。"""
        if not texts:
            return []
        
        url = f"{self.api_base}/embeddings"
        
        # 对于 text-embedding 模型，可以指定维度
        payload = {
            "model": self.model_name,
            "input": texts,
        }
        
        # 如果使用支持维度的 text-embedding 模型，添加维度参数
        if "text-embedding" in self.model_name.lower():
            payload["dimensions"] = self.dimension
        
        client = self._get_client()
        try:
            response = await client.post(
                url,
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            # 提取嵌入向量
            embeddings = [item["embedding"] for item in data["data"]]
            
            # 立即释放data和response的内存
            del data
            del response
            
            return embeddings
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to generate embeddings: {e}")
    
    def generate_embeddings_sync(self, texts: List[str]) -> List[List[float]]:
        """generate_embeddings 的同步版本。"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.generate_embeddings(texts))

