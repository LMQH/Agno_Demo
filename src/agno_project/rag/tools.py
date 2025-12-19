"""RAG 检索工具，供 Agno Agent 调用。"""
from typing import List, Dict, Any, Optional
from agno.tools import Function
from .retriever import RAGRetriever
from ..config import get_config


class RAGRetrievalTool(Function):
    """RAG 检索工具，用于从知识库中检索相关信息。"""
    
    def __init__(self, retriever: Optional[RAGRetriever] = None):
        """初始化 RAG 检索工具。"""
        # 先初始化父类
        super().__init__(
            name="rag_retrieval",
            description="从知识库中检索与查询相关的文档片段。这是回答问题的必要步骤，回答任何问题前都必须先调用此工具从知识库中获取相关信息。",
            args={
                "query": {
                    "type": "string",
                    "description": "要检索的查询文本（通常是用户的问题或关键词）",
                    "required": True
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回的文档片段数量，默认为5",
                    "required": False,
                    "default": 5
                }
            }
        )
        
        # 使用 object.__setattr__ 绕过 Pydantic 的限制
        object.__setattr__(self, '_retriever', retriever or RAGRetriever())
        object.__setattr__(self, '_config', get_config())
        # 保存最后一次检索的原始结果，用于构建 sources（通过 RAGAgent 访问）
        object.__setattr__(self, '_last_results', None)
    
    @property
    def retriever(self) -> RAGRetriever:
        """获取检索器实例。"""
        return object.__getattribute__(self, '_retriever')
    
    @property
    def config(self):
        """获取配置实例。"""
        return object.__getattribute__(self, '_config')
    
    @property
    def last_results(self) -> Optional[List[Dict[str, Any]]]:
        """获取最后一次检索的原始结果。"""
        return object.__getattribute__(self, '_last_results')
    
    async def run(self, query: str, top_k: Optional[int] = None) -> str:
        """执行 RAG 检索。"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"开始执行 RAG 检索，查询: {query[:50]}...")
            top_k = top_k or self.config.rag.top_k
            results = await self.retriever.retrieve(
                query=query,
                top_k=top_k,
                similarity_threshold=self.config.rag.similarity_threshold
            )
            
            # 保存原始结果，供 RAGAgent 构建 sources 使用
            object.__setattr__(self, '_last_results', results)
            logger.info(f"检索完成，找到 {len(results)} 条结果")
            
            if not results:
                logger.warning("未找到相关文档")
                return "未找到相关文档。"
            
            # 格式化检索结果
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"[文档片段 {i}]\n"
                    f"来源文件: {result.get('file_name', '未知')}\n"
                    f"内容: {result['content']}\n"
                    f"相似度得分: {result['score']:.3f}\n"
                )
            
            return "\n".join(formatted_results)
        except Exception as e:
            # 清除结果
            object.__setattr__(self, '_last_results', None)
            logger.error(f"检索过程中发生错误: {e}", exc_info=True)
            return f"检索过程中发生错误: {str(e)}"

