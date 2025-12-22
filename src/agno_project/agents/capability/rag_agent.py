"""RAG 检索 Agent：专门负责从知识库中检索相关文档片段。"""
from typing import Dict, Any, Optional
import logging
from agno.db.mysql import MySQLDb
from ...infrastructure.database.retriever import RAGRetriever
from ...config import get_config

# 配置日志
logger = logging.getLogger(__name__)


class RAGAgent:
    """RAG 检索 Agent：专门负责从知识库中检索相关文档片段。
    
    核心职责：
    - 使用 RAG 检索工具从知识库中检索相关文档片段（chunks）
    - 返回候选的文档片段，不做回答或判断
    
    重要约束：
    - 不回答问题
    - 不做任何判断或分析
    - 不参与后续的讨论或决策
    - 只返回检索到的原始文档片段
    """
    
    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        db: Optional[MySQLDb] = None,
        session_id: Optional[str] = None
    ):
        """初始化 RAG 智能体。
        
        Args:
            retriever: RAG 检索器实例
            db: Agno 数据库实例（当前版本未使用，保留用于兼容）
            session_id: 会话 ID（当前版本未使用，保留用于兼容）
        """
        self.config = get_config()
        self.retriever = retriever or RAGRetriever()
        self.session_id = session_id
        
        # RAG Agent 不再使用 Agent、数据库或 LLM 客户端
        # 直接使用检索器进行检索，更加简单高效
        logger.debug("RAG Agent 初始化完成（仅检索模式，直接使用检索器）")
    
    async def retrieve_chunks(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """检索相关文档片段（chunks）。
        
        Args:
            query: 查询文本
            top_k: 检索的文档片段数量
            similarity_threshold: 相似度阈值
            session_id: 会话 ID（可选，当前版本不使用）
        
        Returns:
            包含查询和检索到的文档片段（chunks）的字典
            格式: {
                "query": str,
                "chunks": List[Dict],  # 每个 chunk 包含 file_id, file_name, content, score
                "num_chunks": int
            }
        """
        logger.debug(f"RAG Agent 开始检索: {query[:50]}...")
        
        # 直接调用检索器，不使用 Agent（因为 Agent 可能会尝试回答或判断）
        try:
            retrieval_results = await self.retriever.retrieve(
                query=query,
                top_k=top_k or self.config.rag.top_k,
                similarity_threshold=similarity_threshold or self.config.rag.similarity_threshold
            )
            
            # 构建 chunks 列表
            chunks = []
            for result in retrieval_results:
                chunks.append({
                    "file_id": result.get("file_id"),
                    "file_name": result.get("file_name", ""),
                    "content": result.get("content", ""),
                    "score": round(result.get("score", 0.0), 4)
                })
            
            logger.debug(f"检索完成，找到 {len(chunks)} 个文档片段")
            
            return {
                "query": query,
                "chunks": chunks,
                "num_chunks": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"检索失败: {e}", exc_info=True)
            return {
                "query": query,
                "chunks": [],
                "num_chunks": 0,
                "error": str(e)
            }
    
    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """查询 RAG 系统（向后兼容方法）。
        
        Args:
            question: 查询文本
            top_k: 检索的文档片段数量
            similarity_threshold: 相似度阈值
            session_id: 会话 ID（未使用，保留用于兼容）
            user_id: 用户 ID（未使用，保留用于兼容）
        
        Returns:
            包含问题、chunks 和来源的字典（向后兼容格式）
            注意：不再生成 answer，只返回 chunks
        """
        # 调用 retrieve_chunks 方法
        result = await self.retrieve_chunks(
            query=question,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            session_id=session_id
        )
        
        # 转换为向后兼容的格式
        return {
            "question": result.get("query", question),
            "answer": "",  # 不再生成答案
            "sources": result.get("chunks", []),  # 使用 chunks 作为 sources
            "chunks": result.get("chunks", []),  # 新增 chunks 字段
            "num_sources": result.get("num_chunks", 0),
            "session_id": session_id
        }
    
