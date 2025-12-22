"""讨论团队：使用 Team 进行多智能体讨论。"""
from typing import Optional, Dict, Any, List
from agno.team.team import Team
from agno.agent import Agent
from agno.db.mysql import MySQLDb

from ...config import get_config
from ...infrastructure.llm.custom_model import CustomModel
from ...tools.rag_retrieval_tool import RAGRetrievalTool
from ...infrastructure.database.retriever import RAGRetriever
from .conservative_agent import ConservativeAgent
from .radical_agent import RadicalAgent
from .official_agent import OfficialAgent
import logging

logger = logging.getLogger(__name__)


class DebateTeam:
    """讨论团队：使用 Team 进行多智能体讨论。
    
    团队结构：
    - Leader: 负责协调队员和控制讨论节奏
    - 队员: 激进、保守、官方三个立场 Agent
    """
    
    def __init__(
        self,
        db: Optional[MySQLDb] = None,
        retriever: Optional[RAGRetriever] = None
    ):
        """初始化讨论团队。"""
        self.config = get_config()
        self.db = db
        self.retriever = retriever or RAGRetriever()
        
        # 创建自定义模型
        custom_model = CustomModel(
            id=self.config.llm.model_name,
            name="Custom DeepSeek Model",
            provider="Custom",
            config=self.config.llm
        )
        
        # 创建队员 Agent
        self.conservative_agent = ConservativeAgent(db=db, retriever=retriever)
        self.radical_agent = RadicalAgent(db=db, retriever=retriever)
        self.official_agent = OfficialAgent(db=db, retriever=retriever)
        
        # 创建 Leader Agent（负责协调）
        leader_agent = Agent(
            name="Debate Leader",
            model=custom_model,
            system_message="""你是讨论团队的 Leader，负责协调队员和控制讨论节奏。

你的职责：
1. 协调队员（激进派、保守派、官方叙事）进行讨论
2. 控制讨论节奏，确保每个立场都有机会表达观点
3. 引导队员针对问题进行深入讨论
4. 整合讨论结果，形成阶段性讨论总结

重要约束：
- 不参与观点生成，只负责协调
- 确保讨论有序进行
- 及时总结讨论要点
- 控制讨论时间，避免无意义的重复""",
        )
        
        # 创建 Team
        self.team = Team(
            name="Debate Team",
            members=[
                leader_agent,
                self.conservative_agent.agent,
                self.radical_agent.agent,
                self.official_agent.agent
            ],
            model=custom_model,
            instructions=[
                "针对用户问题进行多立场讨论",
                "每个队员（激进派、保守派、官方叙事）从自己的立场出发，提出观点并回应其他立场的质疑",
                "Leader 负责协调讨论节奏，确保讨论有序进行",
                "最终形成整合的阶段性讨论结果，明确各立场的核心观点和分歧点"
            ],
            show_members_responses=True,  # 显示成员响应，便于调试
            db=db,
        )
        
        logger.debug("讨论团队初始化完成")
    
    async def debate(
        self,
        question: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        previous_debate: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行讨论。
        
        Args:
            question: 用户问题
            chunks: RAG 检索到的 chunks（可选）
            previous_debate: 之前的讨论结果（可选，用于继续讨论）
            session_id: 会话 ID
            user_id: 用户 ID
            
        Returns:
            讨论结果字典
        """
        logger.info("开始讨论团队讨论...")
        
        # 构建讨论提示
        prompt_parts = [f"问题：{question}"]
        
        # 如果有 chunks，添加到提示中
        if chunks:
            chunks_text = "\n\n".join([
                f"来源：{chunk.get('file_name', '未知')}\n内容：{chunk.get('content', '')}"
                for chunk in chunks[:5]  # 只取前 5 个
            ])
            prompt_parts.append(f"\n相关参考资料：\n{chunks_text}")
        
        # 如果有之前的讨论结果，添加到提示中
        if previous_debate:
            previous_summary = previous_debate.get("summary", "")
            if previous_summary:
                prompt_parts.append(f"\n之前的讨论结果：\n{previous_summary}")
                prompt_parts.append("\n请基于之前的讨论继续深入，提出新的观点或回应质疑。")
        
        prompt = "\n".join(prompt_parts)
        
        # 调用 Team 进行讨论
        try:
            response = await self.team.arun(
                prompt,
                session_id=session_id,
                user_id=user_id
            )
            
            # 提取响应内容
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # 构建讨论结果
            debate_result = {
                "question": question,
                "summary": content,
                "chunks": chunks or [],
                "round": previous_debate.get("round", 0) + 1 if previous_debate else 1
            }
            
            logger.info(f"讨论完成，轮次: {debate_result['round']}")
            return debate_result
            
        except Exception as e:
            logger.error(f"讨论团队执行失败: {e}", exc_info=True)
            return {
                "question": question,
                "summary": f"讨论执行失败: {str(e)}",
                "chunks": chunks or [],
                "round": previous_debate.get("round", 0) + 1 if previous_debate else 1,
                "error": str(e)
            }

