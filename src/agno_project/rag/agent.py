"""基于 Agno Agent 的 RAG 智能体。"""
from typing import List, Dict, Any, Optional
import logging
from agno.agent import Agent
from agno.db.mysql import MySQLDb
from .tools import RAGRetrievalTool
from .llm_client import LLMClient
from .custom_model import CustomModel
from .retriever import RAGRetriever
from ..config import get_config

# 配置日志
logger = logging.getLogger(__name__)


class RAGAgent:
    """基于 Agno Agent 的单智能体 RAG 系统，支持会话持久性。"""
    
    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        db: Optional[MySQLDb] = None,
        session_id: Optional[str] = None
    ):
        """初始化 RAG 智能体。
        
        Args:
            retriever: RAG 检索器实例
            db: Agno 数据库实例（用于会话持久性）
            session_id: 会话 ID（用于多会话支持）
        """
        self.config = get_config()
        self.retriever = retriever or RAGRetriever()
        self.session_id = session_id
        
        # 设置数据库（会话持久性）
        if db is None and self.config.agent_db.enabled:
            logger.info("正在创建 Agno 数据库连接...")
            db = self._create_db()
            logger.info("Agno 数据库连接创建成功")
        elif db is None:
            logger.warning("数据库未启用，记忆功能将不可用")
        
        # 创建 LLM 客户端
        self.llm_client = LLMClient()
        
        # 创建自定义模型实例
        custom_model = CustomModel(
            id=self.config.llm.model_name,
            name="Custom DeepSeek Model",
            provider="Custom",
            config=self.config.llm
        )
        
        # 创建 RAG 检索工具（保存引用以便后续获取检索结果）
        self.rag_tool = RAGRetrievalTool(retriever=self.retriever)
        
        # 初始化 Agno Agent
        # 使用自定义模型类，而不是字符串
        # 构建系统消息，根据是否启用记忆功能来调整
        if db:
            system_message = """你是一个智能问答助手，具有以下能力：
1. 知识库检索：当需要信息时，使用 rag_retrieval 工具从知识库中检索相关内容。
2. 记忆功能：你可以记住和回忆与用户对话中的重要信息，包括用户的偏好、之前讨论过的话题、用户提供的信息等。这些记忆会在后续对话中自动帮助你提供更个性化和连贯的回答。
3. 上下文理解：你可以利用对话历史来理解当前问题的背景，提供更准确的回答。

请充分利用你的记忆功能，记住用户的重要信息，并在后续对话中自然地使用这些记忆来提供更好的服务。"""
            description = "基于知识库的智能问答助手，支持记忆功能和上下文理解，可以从知识库中检索信息并记住用户的重要信息。"
        else:
            system_message = "你是一个有用的问答助手，可以根据知识库中的信息回答问题。当需要信息时，使用 rag_retrieval 工具从知识库中检索相关内容。"
            description = "基于知识库的问答助手，可以从知识库中检索信息并回答问题。"
        
        # 构建 Agent 配置参数
        agent_kwargs = {
            "name": "RAG Agent",
            "model": custom_model,
            "tools": [self.rag_tool],
            "system_message": system_message,
        }
        
        # 如果提供了数据库，添加会话持久性、历史记录和记忆功能
        if db:
            agent_kwargs["db"] = db
            agent_kwargs["session_id"] = self.session_id
            agent_kwargs["add_history_to_context"] = True
            agent_kwargs["num_history_runs"] = 2  # 简化配置，使用固定值
            agent_kwargs["enable_user_memories"] = True
            agent_kwargs["add_memories_to_context"] = True
            logger.info("已启用会话持久性、历史记录和记忆功能（历史记录数量: 2）")
        else:
            logger.warning("未提供数据库连接，记忆功能将不可用")
        
        self.agent = Agent(**agent_kwargs)
        logger.info("RAG Agent 初始化完成")
    
    def _create_db(self) -> MySQLDb:
        """创建 Agno 数据库实例，使用 MySQLDb 连接 MySQL。"""
        mysql_config = self.config.mysql
        
        # 构建 MySQL 连接字符串
        # 格式: mysql+pymysql://user:password@host:port/database
        db_url = (
            f"mysql+pymysql://{mysql_config.user}:{mysql_config.password}"
            f"@{mysql_config.host}:{mysql_config.port}/{mysql_config.database}"
        )
        
        # 如果配置了 charset，添加到连接字符串
        if mysql_config.charset:
            db_url += f"?charset={mysql_config.charset}"
        
        logger.info(f"创建 MySQL 数据库连接: {mysql_config.host}:{mysql_config.port}/{mysql_config.database}")
        db = MySQLDb(db_url=db_url)
        logger.info("MySQL 数据库连接创建成功，Agno 将在首次使用时自动创建必要的表")
        return db
    
    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """查询 RAG 系统。
        
        Args:
            question: 用户问题
            top_k: 检索的文档片段数量
            similarity_threshold: 相似度阈值
            session_id: 会话 ID（用于会话持久性）
            user_id: 用户 ID（用于记忆功能，区分不同用户的记忆）
        
        Returns:
            包含问题、答案和来源的字典
        """
        # 使用提供的 session_id 或实例的 session_id
        current_session_id = session_id or self.session_id
        if current_session_id:
            logger.info(f"使用会话 ID: {current_session_id}")
        else:
            logger.warning("未提供会话 ID，记忆功能可能无法正常工作")
        
        # 使用 user_id 或 session_id 作为 user_id（如果未提供）
        # 根据 Agno 文档，记忆功能需要 user_id 来区分不同用户
        current_user_id = user_id or current_session_id or "default_user"
        if current_user_id:
            logger.info(f"使用用户 ID: {current_user_id}")
        
        # 调用 Agno Agent 的 arun 方法（异步版本）
        # Agent 会自动使用 rag_retrieval 工具进行检索
        # 注意：不再预先检索，避免重复检索和 sources 不一致的问题
        try:
            response = await self.agent.arun(
                question,
                session_id=current_session_id,
                user_id=current_user_id  # 传递 user_id 以启用记忆功能
            )
            
            # 提取答案
            if hasattr(response, 'content'):
                answer = response.content
            elif hasattr(response, 'messages') and response.messages:
                # 从消息中提取最后一条助手消息
                for msg in reversed(response.messages):
                    if hasattr(msg, 'content') and msg.content:
                        answer = msg.content
                        break
                else:
                    answer = str(response)
            else:
                answer = str(response)
            
            # 从工具中获取最后一次检索的结果来构建 sources
            # 这样 sources 和 Agent 使用的 context 是完全一致的
            sources = []
            if hasattr(self.rag_tool, 'last_results') and self.rag_tool.last_results:
                retrieval_results = self.rag_tool.last_results
                for result in retrieval_results:
                    sources.append({
                        "file_id": result.get("file_id"),
                        "file_name": result.get("file_name", ""),
                        "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),  # 只返回前200字符作为预览
                        "score": round(result.get("score", 0.0), 4)
                    })
            else:
                logger.warning("无法从工具中获取检索结果，sources 为空（Agent 可能未调用检索工具）")
                
        except Exception as e:
            logger.error(f"Agent 调用失败: {e}", exc_info=True)
            # 如果 Agent 调用失败，回退到直接使用 LLM
            # 此时需要检索来构建上下文
            retrieval_results = await self.retriever.retrieve(
                query=question,
                top_k=top_k or self.config.rag.top_k,
                similarity_threshold=similarity_threshold or self.config.rag.similarity_threshold
            )
            
            # 构建 sources
            sources = []
            for result in retrieval_results:
                sources.append({
                    "file_id": result.get("file_id"),
                    "file_name": result.get("file_name", ""),
                    "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                    "score": round(result.get("score", 0.0), 4)
                })
            
            # 构建上下文
            context = "\n\n".join([r['content'] for r in retrieval_results]) if retrieval_results else ""
            
            # 使用 LLM 生成答案
            system_prompt = "你是一个有用的助手，可以根据提供的知识库内容回答问题。"
            prompt = f"基于以下知识库内容回答问题：\n\n{context}\n\n问题：{question}\n\n答案："
            answer = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt
            )
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "session_id": current_session_id,
            "num_sources": len(sources)
        }
    
    def get_session_history(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取会话历史记录。
        
        Args:
            session_id: 会话 ID，如果为 None 则使用当前会话 ID
        
        Returns:
            会话历史记录列表
        """
        current_session_id = session_id or self.session_id
        if not current_session_id or not self.agent.db:
            return []
        
        # 从数据库获取会话历史
        # 这里需要根据 Agno 的 API 来实现
        # 注意：具体实现取决于 Agno 的版本和 API
        try:
            # 假设 Agno 提供了获取历史的方法
            if hasattr(self.agent.db, 'get_session'):
                session = self.agent.db.get_session(current_session_id)
                if session:
                    return session.get('messages', [])
        except Exception:
            pass
        
        return []

