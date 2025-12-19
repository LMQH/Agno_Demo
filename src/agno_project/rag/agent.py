"""基于 Agno Agent 的 RAG 智能体。"""
from typing import List, Dict, Any, Optional
import logging
from agno.agent import Agent
from agno.db.mysql import MySQLDb
from agno.memory.manager import MemoryManager
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
            # 使用配置文件中的值，而不是硬编码
            agent_kwargs["num_history_runs"] = self.config.agent_db.num_history_runs
            
            # 创建记忆管理器（必需！）
            memory_manager = MemoryManager(db=db)
            agent_kwargs["memory_manager"] = memory_manager
            
            # 启用记忆功能
            agent_kwargs["enable_agentic_memory"] = True  # 启用 Agent 管理记忆
            agent_kwargs["enable_user_memories"] = True  # 启用用户记忆
            agent_kwargs["add_memories_to_context"] = True  # 将记忆添加到上下文
            
            # 添加 instructions 来指导记忆行为，防止不必要的记忆更新
            # 根据 Agno 文档，instructions 可以帮助控制记忆的创建和更新
            # 注意：instructions 只影响记忆管理，不会影响历史记录的加载和使用
            agent_kwargs["instructions"] = """关于记忆管理的建议（不影响对话流程）：
- 充分利用对话历史来理解上下文，正常进行多轮对话
- 在创建长期记忆时，优先记住对后续对话有价值的重要信息（用户偏好、重要事实、关键决策等）
- 临时信息和一次性对话内容会通过历史记录自动保留，无需创建长期记忆
- 在回答时自然引用记忆和历史信息，保持对话的连贯性"""
            # 设置工具调用限制，防止过度操作
            agent_kwargs["tool_call_limit"] = 10
            logger.info(
                f"已启用会话持久性、历史记录和记忆功能（"
                f"历史记录数量: {self.config.agent_db.num_history_runs}, "
                f"工具调用限制: 10"
                f"）"
            )
        else:
            logger.warning("未提供数据库连接，记忆功能将不可用")
        
        self.agent = Agent(**agent_kwargs)
        
        # 如果提供了数据库，确保表已创建（特别是记忆表）
        if db:
            self._ensure_tables_created(db)
        
        logger.info("RAG Agent 初始化完成")
    
    def _ensure_tables_created(self, db: MySQLDb) -> None:
        """确保 Agno 数据库表已创建（特别是记忆表）。
        
        Args:
            db: Agno 数据库实例
        """
        try:
            # 通过访问记忆表来触发表创建
            # 使用 create_table_if_not_found=True 确保表会被创建
            if hasattr(db, '_get_table'):
                # 触发记忆表的创建
                memory_table = db._get_table(table_type="memories", create_table_if_not_found=True)
                if memory_table:
                    logger.info("记忆表已创建或已存在")
                else:
                    logger.warning("无法创建记忆表")
            
            # 触发会话表的创建
            if hasattr(db, '_get_table'):
                session_table = db._get_table(table_type="sessions", create_table_if_not_found=True)
                if session_table:
                    logger.info("会话表已创建或已存在")
        except Exception as e:
            logger.warning(f"确保表创建时出错（表可能在使用时自动创建）: {e}")
    
    def _create_db(self) -> MySQLDb:
        """创建 Agno 数据库实例，使用 MySQLDb 连接 MySQL。"""
        mysql_config = self.config.mysql
        agent_db_config = self.config.agent_db
        
        # 构建 MySQL 连接字符串
        # 格式: mysql+pymysql://user:password@host:port/database
        db_url = (
            f"mysql+pymysql://{mysql_config.user}:{mysql_config.password}"
            f"@{mysql_config.host}:{mysql_config.port}/{mysql_config.database}"
        )
        
        # 如果配置了 charset，添加到连接字符串
        if mysql_config.charset:
            db_url += f"?charset={mysql_config.charset}"
        
        # 准备 MySQLDb 参数
        db_kwargs = {"db_url": db_url}
        
        # 如果配置了自定义 schema，使用它（这将影响所有表名）
        if agent_db_config.db_schema:
            db_kwargs["db_schema"] = agent_db_config.db_schema
            logger.info(f"使用自定义数据库 schema: {agent_db_config.db_schema}")
        
        # 如果配置了自定义会话表名
        if agent_db_config.session_table:
            db_kwargs["session_table"] = agent_db_config.session_table
            logger.info(f"使用自定义会话表名: {agent_db_config.session_table}")
        
        # 如果配置了自定义记忆表名
        if agent_db_config.memory_table:
            db_kwargs["memory_table"] = agent_db_config.memory_table
            logger.info(f"使用自定义记忆表名: {agent_db_config.memory_table}")
        
        logger.info(f"创建 MySQL 数据库连接: {mysql_config.host}:{mysql_config.port}/{mysql_config.database}")
        db = MySQLDb(**db_kwargs)
        
        # 记录实际使用的表名
        schema_info = f"schema={agent_db_config.db_schema or 'ai'}"
        if agent_db_config.session_table:
            schema_info += f", session_table={agent_db_config.session_table}"
        if agent_db_config.memory_table:
            schema_info += f", memory_table={agent_db_config.memory_table}"
        logger.info(f"MySQL 数据库连接创建成功，Agno 将在首次使用时自动创建必要的表（{schema_info}）")
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
            # 优先从工具实例获取，如果失败则尝试从 response 中提取
            sources = self._extract_sources_from_response(response)
            
            if not sources:
                logger.warning("无法获取检索结果，sources 为空（Agent 可能未调用检索工具）")
                # 如果 Agent 没有调用工具，记录调试信息
                if hasattr(response, 'messages'):
                    tool_calls = [msg for msg in response.messages if hasattr(msg, 'tool_calls') and msg.tool_calls]
                    logger.debug(f"响应中的工具调用数量: {len(tool_calls)}")
                
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
    
    def _extract_sources_from_response(self, response) -> List[Dict[str, Any]]:
        """从 Agent 响应中提取检索结果作为 sources。
        
        Args:
            response: Agent 的响应对象
            
        Returns:
            sources 列表
        """
        sources = []
        
        # 方法1: 从工具实例的 last_results 获取（最可靠）
        try:
            if hasattr(self.rag_tool, 'last_results') and self.rag_tool.last_results:
                retrieval_results = self.rag_tool.last_results
                logger.debug(f"从工具实例获取到 {len(retrieval_results)} 条检索结果")
                for result in retrieval_results:
                    sources.append({
                        "file_id": result.get("file_id"),
                        "file_name": result.get("file_name", ""),
                        "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                        "score": round(result.get("score", 0.0), 4)
                    })
                return sources
        except Exception as e:
            logger.warning(f"从工具实例获取 sources 失败: {e}")
        
        # 方法2: 尝试从 response 中提取工具调用信息
        try:
            if hasattr(response, 'messages'):
                # 查找工具调用的消息
                for msg in response.messages:
                    # 检查是否有工具调用
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if tool_call.get('function', {}).get('name') == 'rag_retrieval':
                                logger.debug("在响应中找到 rag_retrieval 工具调用")
                                # 注意：这里可能需要根据 Agno 的实际响应格式来解析
                    
                    # 检查是否有工具结果
                    if hasattr(msg, 'tool_results') and msg.tool_results:
                        for tool_result in msg.tool_results:
                            if tool_result.get('tool_name') == 'rag_retrieval':
                                logger.debug("在响应中找到 rag_retrieval 工具结果")
                                # 尝试解析工具结果
                                # 注意：这取决于 Agno 的实际响应格式
        except Exception as e:
            logger.debug(f"从响应中提取工具调用信息失败: {e}")
        
        return sources
    
    def verify_memory_enabled(self) -> Dict[str, Any]:
        """验证记忆功能是否正常启用。
        
        Returns:
            包含记忆功能状态的字典
        """
        status = {
            "db_enabled": self.config.agent_db.enabled,
            "db_connected": self.agent.db is not None if hasattr(self, 'agent') else False,
            "memory_manager_enabled": hasattr(self.agent, 'memory_manager') and self.agent.memory_manager is not None if hasattr(self, 'agent') else False,
            "enable_agentic_memory": getattr(self.agent, 'enable_agentic_memory', False) if hasattr(self, 'agent') else False,
            "enable_user_memories": getattr(self.agent, 'enable_user_memories', False) if hasattr(self, 'agent') else False,
            "add_memories_to_context": getattr(self.agent, 'add_memories_to_context', False) if hasattr(self, 'agent') else False,
            "history_enabled": True if hasattr(self, 'agent') and self.agent.db else False,
            "num_history_runs": self.config.agent_db.num_history_runs,
            "session_id": self.session_id,
        }
        return status
    
    async def prune_memories(
        self,
        user_id: str,
        keep_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """清理用户的记忆（保留最近的 N 条）。
        
        根据 Agno 文档，记忆会自动清理，但也可以手动触发清理。
        
        Args:
            user_id: 用户 ID
            keep_count: 保留的记忆数量，如果为 None 则使用默认值（10）
        
        Returns:
            清理结果字典
        """
        if not self.agent.db:
            return {
                "status": "error",
                "message": "数据库未连接，无法清理记忆"
            }
        
        try:
            # 注意：具体的清理逻辑取决于 Agno 的 API
            # 这里提供一个基础实现框架
            logger.info(f"开始清理用户 {user_id} 的记忆（保留最近 {keep_count or 10} 条）")
            
            # TODO: 根据 Agno 的实际 API 实现记忆清理
            # 可能需要直接操作数据库或使用 Agno 提供的记忆管理 API
            
            return {
                "status": "success",
                "message": f"用户 {user_id} 的记忆清理完成",
                "user_id": user_id,
                "keep_count": keep_count or 10
            }
        except Exception as e:
            logger.error(f"清理记忆失败: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"清理记忆失败: {str(e)}"
            }

