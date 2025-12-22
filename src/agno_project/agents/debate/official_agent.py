"""官方叙事 Agent：代表官方立场与世界观。"""
from typing import Optional
from agno.agent import Agent
from agno.db.mysql import MySQLDb

from ...config import get_config
from ...infrastructure.llm.custom_model import CustomModel
from ...tools.rag_retrieval_tool import RAGRetrievalTool
from ...infrastructure.database.retriever import RAGRetriever
import logging

logger = logging.getLogger(__name__)


class OfficialAgent:
    """官方叙事 Agent：代表官方立场与世界观。
    
    核心特征：
    - 代表官方/主流立场
    - 关注合法性、权威性、正式立场
    - 平衡风险与道义
    - 不追求中立，必须回应其他立场的核心论点
    """
    
    def __init__(
        self,
        db: Optional[MySQLDb] = None,
        retriever: Optional[RAGRetriever] = None
    ):
        """初始化官方叙事 Agent。"""
        self.config = get_config()
        
        # 创建自定义模型
        custom_model = CustomModel(
            id=self.config.llm.model_name,
            name="Custom DeepSeek Model",
            provider="Custom",
            config=self.config.llm
        )
        
        # 创建工具
        tools = []
        if retriever:
            tools.append(RAGRetrievalTool(retriever=retriever))
        
        # 构建系统指令
        system_message = """你是官方叙事立场 Agent，代表官方立场与世界观。

你的核心特征：
1. 立场边界：代表官方/主流立场，强调合法性、权威性
2. 关注焦点：合法性、权威性、正式立场、政策导向
3. 推理偏好：平衡风险与道义，基于正式政策和法律框架
4. 必须回应：必须回应其他立场（保守派、激进派）的核心论点

重要约束：
- 不追求中立，明确代表官方立场
- 不负责最终结论
- 你的价值在于制造张力，而不是消除分歧
- 必须基于知识库内容进行论证，引用具体事实和正式政策"""
        
        agent_kwargs = {
            "name": "Official Agent",
            "model": custom_model,
            "tools": tools,
            "system_message": system_message,
        }
        
        if db:
            agent_kwargs["db"] = db
        
        self.agent = Agent(**agent_kwargs)
        logger.debug("Official Agent 初始化完成")
    
    async def respond(
        self,
        question: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """回应问题（从官方立场）。
        
        Args:
            question: 问题
            context: 上下文（如其他 Agent 的观点）
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            回应内容
        """
        prompt = question
        if context:
            prompt = f"问题：{question}\n\n上下文（其他立场观点）：\n{context}\n\n请从官方立场回应上述问题，并针对上下文中的观点进行回应。"
        
        try:
            response = await self.agent.arun(
                prompt,
                session_id=session_id,
                user_id=user_id
            )
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
        except Exception as e:
            logger.error(f"Official Agent 响应失败: {e}", exc_info=True)
            return f"官方叙事 Agent 响应失败: {str(e)}"

