"""用于语义搜索的 RAG 检索器。"""
from typing import List, Dict, Any, Optional
from ..database.milvus_client import MilvusClient
from ..knowledge_base.embedder import EmbeddingGenerator
from ..config import get_config


class RAGRetriever:
    """为 RAG 检索相关文档。"""
    
    def __init__(
        self,
        milvus_client: Optional[MilvusClient] = None,
        embedder: Optional[EmbeddingGenerator] = None
    ):
        """初始化 RAG 检索器。"""
        self.milvus_client = milvus_client or MilvusClient()
        self.embedder = embedder or EmbeddingGenerator()
        self.config = get_config()
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """为查询检索相关切片。"""
        top_k = top_k or self.config.rag.top_k
        threshold = similarity_threshold or self.config.rag.similarity_threshold
        
        # 生成查询嵌入向量
        query_embeddings = await self.embedder.generate_embeddings([query])
        
        # 在 Milvus 中搜索
        search_results = self.milvus_client.search_vectors(
            query_embeddings=query_embeddings,
            top_k=top_k * 2,  # 获取更多结果用于过滤
            output_fields=["file_id", "file_name", "content"]
        )
        
        # 按相似度阈值过滤并格式化结果
        results = []
        if search_results and len(search_results) > 0:
            for hit in search_results[0]:
                if hit["score"] >= threshold:
                    results.append({
                        "file_id": hit["file_id"],
                        "file_name": hit["file_name"],
                        "content": hit["content"],
                        "score": hit["score"]
                    })
                if len(results) >= top_k:
                    break
        
        return results

