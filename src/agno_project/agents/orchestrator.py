"""多智能体系统协调器。"""
from typing import Dict, Any, Optional, List
from agno.db.mysql import MySQLDb
import logging

from .planning.planner_agent import PlannerAgent
from .capability.rag_agent import RAGAgent
from .debate.conservative_agent import ConservativeAgent
from .debate.radical_agent import RadicalAgent
from .debate.official_agent import OfficialAgent
from .judgment.judge_agent import JudgeAgent
from .terminal.reply_agent import ReplyAgent
from ..protocols.plan_schema import PlanOutput, ProcessingPath
from ..protocols.debate_protocol import DebateProtocol, DebateState, DebateRound, DebateStatus, TerminationReason
from ..infrastructure.database.retriever import RAGRetriever
from ..config import get_config

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """多智能体系统协调器。
    
    负责协调各个 Agent 的工作流程：
    1. Router Agent 分析问题并制定计划
    2. 根据计划执行相应的处理路径
    3. 如果是多智能体讨论，协调讨论流程
    4. Eval Agent 评估讨论质量
    5. Reply Agent 生成最终回答
    """
    
    def __init__(
        self,
        db: Optional[MySQLDb] = None,
        retriever: Optional[RAGRetriever] = None
    ):
        """初始化多智能体协调器。"""
        self.config = get_config()
        self.db = db
        self.retriever = retriever or RAGRetriever()
        
        # 初始化各个 Agent
        logger.info("正在初始化多智能体系统...")
        self.planner = PlannerAgent(db=db, retriever=self.retriever)
        self.rag_agent = RAGAgent(retriever=self.retriever, db=db)
        self.conservative_agent = ConservativeAgent(db=db, retriever=self.retriever)
        self.radical_agent = RadicalAgent(db=db, retriever=self.retriever)
        self.official_agent = OfficialAgent(db=db, retriever=self.retriever)
        self.judge_agent = JudgeAgent(db=db)
        self.reply_agent = ReplyAgent(db=db)
        
        logger.info("多智能体系统初始化完成")
    
    async def process(
        self,
        question: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理用户问题。
        
        Args:
            question: 用户问题
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            处理结果字典
        """
        logger.info(f"开始处理问题: {question[:100]}...")
        
        # 步骤 1: Router Agent 制定计划
        plan = await self.planner.plan(question, session_id=session_id, user_id=user_id)
        logger.info(f"Router Agent 决策: {plan.processing_path.value}, 复杂度: {plan.complexity_level.value}, 风险: {plan.risk_level.value}")
        
        # 步骤 2: 根据计划执行相应的处理路径
        if plan.processing_path == ProcessingPath.REJECT:
            return {
                "question": question,
                "answer": f"抱歉，根据安全策略，无法处理该问题。原因：{plan.reasoning}",
                "sources": [],
                "num_sources": 0,
                "session_id": session_id,
                "processing_path": plan.processing_path.value,
                "plan": plan.dict()
            }
        
        elif plan.processing_path == ProcessingPath.DIRECT_TOOL:
            # 直接工具执行（使用 RAG Agent）
            result = await self.rag_agent.query(
                question=question,
                session_id=session_id,
                user_id=user_id
            )
            return {
                **result,
                "processing_path": plan.processing_path.value,
                "plan": plan.dict()
            }
        
        elif plan.processing_path == ProcessingPath.DEGRADED_ANALYSIS:
            # 降级处理：使用 RAG Agent 但应用限制
            # TODO: 实现降级处理逻辑（限制 Agent 的行为）
            result = await self.rag_agent.query(
                question=question,
                session_id=session_id,
                user_id=user_id
            )
            return {
                **result,
                "processing_path": plan.processing_path.value,
                "plan": plan.dict(),
                "degraded": True
            }
        
        elif plan.processing_path == ProcessingPath.MULTI_AGENT_DEBATE:
            # 多智能体讨论
            debate_result = await self._run_debate(
                question=question,
                plan=plan,
                session_id=session_id,
                user_id=user_id
            )
            
            # 使用 Reply Agent 生成最终回答
            final_answer = await self.reply_agent.generate_reply(
                question=question,
                debate_state=debate_result["debate_state"],
                session_id=session_id,
                user_id=user_id
            )
            
            return {
                "question": question,
                "answer": final_answer,
                "sources": debate_result.get("sources", []),
                "num_sources": len(debate_result.get("sources", [])),
                "session_id": session_id,
                "processing_path": plan.processing_path.value,
                "plan": plan.dict(),
                "debate_state": debate_result["debate_state"].dict() if hasattr(debate_result["debate_state"], "dict") else None
            }
        
        else:
            # 未知处理路径，使用默认处理
            logger.warning(f"未知处理路径: {plan.processing_path}")
            result = await self.rag_agent.query(
                question=question,
                session_id=session_id,
                user_id=user_id
            )
            return {
                **result,
                "processing_path": plan.processing_path.value,
                "plan": plan.dict()
            }
    
    async def _run_debate(
        self,
        question: str,
        plan: PlanOutput,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行多智能体讨论。
        
        Args:
            question: 问题
            plan: 处理计划
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            讨论结果字典
        """
        logger.info("开始多智能体讨论...")
        
        # 确定参与讨论的 Agent
        allowed_agents = plan.allowed_agents or ["conservative", "radical", "official"]
        max_rounds = plan.max_debate_rounds or 3
        
        # 初始化讨论状态
        debate_state = DebateState(
            status=DebateStatus.ONGOING,
            current_round=0,
            max_rounds=max_rounds,
            participants=allowed_agents,
            rounds=[]
        )
        
        # Agent 映射
        agent_map = {
            "conservative": self.conservative_agent,
            "radical": self.radical_agent,
            "official": self.official_agent
        }
        
        # 讨论循环
        while debate_state.status == DebateStatus.ONGOING:
            # 检查是否应该终止
            should_terminate, reason = DebateProtocol.should_terminate(debate_state)
            if should_terminate:
                debate_state.status = DebateStatus.TERMINATED
                debate_state.termination_reason = reason
                logger.info(f"讨论终止，原因: {reason.value}")
                break
            
            # 获取下一个发言者
            next_speaker = DebateProtocol.get_next_speaker(debate_state, allowed_agents)
            if not next_speaker:
                logger.warning("无法确定下一个发言者，终止讨论")
                debate_state.status = DebateStatus.TERMINATED
                debate_state.termination_reason = TerminationReason.MAX_ROUNDS_REACHED
                break
            
            # 获取 Agent 实例
            agent = agent_map.get(next_speaker)
            if not agent:
                logger.warning(f"未找到 Agent: {next_speaker}")
                debate_state.status = DebateStatus.TERMINATED
                break
            
            # 构建上下文（其他 Agent 的观点）
            context = self._build_context(debate_state.rounds)
            
            # Agent 发言
            try:
                response = await agent.respond(
                    question=question,
                    context=context,
                    session_id=session_id,
                    user_id=user_id
                )
                
                # 记录轮次
                debate_state.current_round += 1
                debate_state.rounds.append(DebateRound(
                    round_number=debate_state.current_round,
                    agent_name=next_speaker,
                    content=response,
                    responds_to=None  # TODO: 实现更智能的回应关系追踪
                ))
                
                logger.info(f"轮次 {debate_state.current_round}: {next_speaker} 已完成发言")
            except Exception as e:
                logger.error(f"Agent {next_speaker} 发言失败: {e}", exc_info=True)
                debate_state.status = DebateStatus.TERMINATED
                break
            
            # 每轮后使用 Eval Agent 评估（可选，可以每 N 轮评估一次）
            if debate_state.current_round % 2 == 0:  # 每 2 轮评估一次
                eval_result = await self.judge_agent.evaluate(
                    debate_state=debate_state,
                    question=question,
                    session_id=session_id,
                    user_id=user_id
                )
                
                if eval_result.action.value == "terminate":
                    debate_state.status = DebateStatus.TERMINATED
                    debate_state.termination_reason = TerminationReason.EVAL_RECOMMENDATION
                    logger.info("Eval Agent 建议终止讨论")
                    break
        
        # 讨论完成
        if debate_state.current_round >= debate_state.max_rounds:
            debate_state.status = DebateStatus.COMPLETED
            logger.info(f"讨论完成，共 {debate_state.current_round} 轮")
        
        # TODO: 从讨论中提取 sources
        sources = []
        
        return {
            "debate_state": debate_state,
            "sources": sources
        }
    
    def _build_context(self, rounds: List[DebateRound]) -> str:
        """构建上下文（其他 Agent 的观点）。
        
        Args:
            rounds: 讨论轮次列表
        
        Returns:
            上下文字符串
        """
        if not rounds:
            return ""
        
        context_parts = []
        for round_info in rounds[-3:]:  # 只取最近 3 轮
            context_parts.append(f"{round_info.agent_name}: {round_info.content}")
        
        return "\n\n".join(context_parts)

