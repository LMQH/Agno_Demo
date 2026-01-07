"""工作流控制器：使用 Workflow 控制全流程，内部使用 Team 进行讨论。"""
from typing import Dict, Any, Optional, List
from agno.workflow.workflow import Workflow
from agno.db.mysql import MySQLDb
import logging

from .planning.planner_agent import PlannerAgent
from .capability.rag_agent import RAGAgent
from .judgment.judge_agent import JudgeAgent
from .terminal.reply_agent import ReplyAgent
from .debate.debate_team import DebateTeam
from ..protocols.plan_schema import PlanOutput, ProcessingPath
from ..protocols.judgment_rules import JudgmentAction
from ..infrastructure.database.retriever import RAGRetriever
from ..config import get_config

logger = logging.getLogger(__name__)


class WorkflowController:
    """工作流控制器：使用 Workflow 控制全流程。
    
    流程：
    1. Planning 智能体：判断启用的智能体（是否需要 RAG，是否需要讨论团队）
    2. RAG 智能体：调用工具进行检索召回，只返回 chunk 候选
    3. 讨论团队：由 Team 定义，leader 负责协调，队员进行辩论
    4. 判断智能体：控制讨论是否停止，是否回到 RAG 再检索
    5. 整合输出智能体：根据传入结果整合输出
    """
    
    def __init__(
        self,
        db: Optional[MySQLDb] = None,
        retriever: Optional[RAGRetriever] = None
    ):
        """初始化工作流控制器。"""
        self.config = get_config()
        self.db = db
        self.retriever = retriever or RAGRetriever()
        
        # 初始化各个智能体
        logger.info("正在初始化工作流控制器...")
        self.planner = PlannerAgent(db=db, retriever=self.retriever)
        self.rag_agent = RAGAgent(retriever=self.retriever, db=db)
        self.judge_agent = JudgeAgent(db=db)
        self.reply_agent = ReplyAgent(db=db)
        
        # 创建讨论团队
        self.debate_team = DebateTeam(db=db, retriever=self.retriever)
        
        # 创建 Workflow（使用 lambda 绑定实例方法）
        # 根据 Agno Workflow 源码，steps 函数的参数传递机制：
        # 1. 如果函数签名中有 execution_input 参数，框架会传递 WorkflowExecutionInput 对象
        # 2. 如果函数签名中有 session_state 参数，框架会传递 self.session_state
        # 3. workflow.arun() 的自定义参数（如 query）会通过 **kwargs 传递
        # 4. session_id 和 user_id 是标准参数，不会在 kwargs 中，需要通过 execution_input.additional_data 获取
        async def workflow_steps_wrapper(
            session_state: Optional[Dict[str, Any]] = None,
            execution_input: Optional[Any] = None,
            **kwargs
        ):
            # 确保 session_state 不为 None
            if session_state is None:
                session_state = {}
            
            # 从 kwargs 中提取自定义参数（workflow.arun() 的自定义参数会通过 kwargs 传递）
            query = kwargs.pop("query", None)
            
            # 从 execution_input 获取参数（这是标准方式）
            session_id = None
            user_id = None
            if execution_input:
                # 从 execution_input.input 获取 query
                if query is None and hasattr(execution_input, "input"):
                    input_data = execution_input.input
                    if isinstance(input_data, str):
                        query = input_data
                    elif isinstance(input_data, dict):
                        query = input_data.get("query") or input_data.get("question")
                
                # 从 execution_input.additional_data 获取 session_id 和 user_id
                if hasattr(execution_input, "additional_data") and execution_input.additional_data:
                    session_id = execution_input.additional_data.get("session_id")
                    user_id = execution_input.additional_data.get("user_id")
            
            # 如果 query 不存在，尝试从 session_state 获取
            if query is None:
                query = session_state.get("query")
            
            # 如果 query 仍然不存在，尝试从 session_state 的 input 字段获取
            if query is None and "input" in session_state:
                input_data = session_state["input"]
                if isinstance(input_data, dict):
                    query = input_data.get("query") or input_data.get("question")
                elif isinstance(input_data, str):
                    query = input_data
            
            # 如果 session_id 和 user_id 不存在，尝试从 session_state 获取
            if session_id is None:
                session_id = session_state.get("session_id")
            if user_id is None:
                user_id = session_state.get("user_id")
            
            # 如果仍然没有 query，抛出错误
            if query is None:
                raise ValueError("query 参数未提供，无法执行工作流。请确保 workflow.arun() 调用时传递了 input 参数。")
            
            # 调用 _workflow_steps，注意已经从 kwargs 中移除了 query
            return await self._workflow_steps(
                session_state=session_state,
                query=query,
                session_id=session_id,
                user_id=user_id,
                **kwargs  # 剩余的 kwargs（不包含 query）
            )
        
        self.workflow = Workflow(
            name="Multi-Agent Workflow",
            steps=workflow_steps_wrapper,
            db=db,
        )
        
        logger.info("工作流控制器初始化完成")
    
    async def _workflow_steps(
        self,
        session_state: Dict[str, Any],
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs  # 接受额外参数（如 websocket），避免函数签名检查失败
    ) -> Dict[str, Any]:
        """工作流步骤定义。
        
        Args:
            session_state: 会话状态
            query: 用户查询
            session_id: 会话 ID
            user_id: 用户 ID
            
        Returns:
            最终结果字典
        """
        logger.info(f"开始处理查询: {query[:100]}...")
        
        # 步骤 1: Planning 智能体判断启用的智能体
        plan = await self.planner.plan(
            query,
            session_id=session_id,
            user_id=user_id
        )
        logger.info(
            f"Planning 决策: {plan.processing_path.value}, "
            f"复杂度: {plan.complexity_level.value}, "
            f"风险: {plan.risk_level.value}, "
            f"需要检索: {plan.requires_retrieval}"
        )
        
        # 如果拒绝处理，直接返回
        if plan.processing_path == ProcessingPath.REJECT:
            return {
                "question": query,
                "answer": f"抱歉，根据安全策略，无法处理该问题。原因：{plan.reasoning}",
                "sources": [],
                "num_sources": 0,
                "session_id": session_id,
                "processing_path": plan.processing_path.value,
                "plan": plan.dict()
            }
        
        # 初始化结果
        chunks = []
        debate_result = None
        judgment_result = None
        
        # 步骤 2: 如果需要检索，调用 RAG 智能体
        if plan.requires_retrieval:
            rag_result = await self.rag_agent.retrieve_chunks(
                query=query,
                session_id=session_id
            )
            chunks = rag_result.get("chunks", [])
            logger.info(f"RAG 检索完成，找到 {len(chunks)} 个 chunks")
        
        # 步骤 3: 如果需要讨论团队，进入讨论流程
        if plan.processing_path == ProcessingPath.MULTI_AGENT_DEBATE:
            # 讨论循环：由 judge_agent 控制是否继续
            max_iterations = 5  # 最大迭代次数，防止无限循环
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"讨论迭代 {iteration}/{max_iterations}")
                
                # 调用讨论团队进行讨论
                debate_result = await self.debate_team.debate(
                    question=query,
                    chunks=chunks,
                    previous_debate=debate_result,
                    session_id=session_id,
                    user_id=user_id
                )
                
                # 步骤 4: 判断智能体评估讨论结果
                judgment_result = await self.judge_agent.evaluate(
                    debate_result=debate_result,
                    question=query,
                    chunks=chunks,
                    session_id=session_id,
                    user_id=user_id
                )
                
                logger.info(
                    f"判断结果: action={judgment_result.action.value}, "
                    f"reasoning={judgment_result.reasoning[:100]}..."
                )
                
                # 如果判断应该终止，退出循环
                if judgment_result.action == JudgmentAction.TERMINATE or judgment_result.action.value == "terminate":
                    logger.info("判断智能体决定终止讨论")
                    break
                
                # 如果判断需要重新检索，回到 RAG
                if judgment_result.action == JudgmentAction.REQUEST_RAG or judgment_result.action.value == "request_rag":
                    logger.info("判断智能体决定重新检索 RAG")
                    rag_result = await self.rag_agent.retrieve_chunks(
                        query=query,
                        session_id=session_id
                    )
                    chunks = rag_result.get("chunks", [])
                    logger.info(f"重新检索完成，找到 {len(chunks)} 个 chunks")
                    # 继续下一轮讨论
                    continue
                
                # 如果判断继续讨论，进入下一轮
                if judgment_result.action == JudgmentAction.CONTINUE or judgment_result.action.value == "continue":
                    logger.info("判断智能体决定继续讨论")
                    continue
                
                # 其他情况，默认终止
                logger.warning(f"未知的判断动作: {judgment_result.action.value}，终止讨论")
                break
        
        # 步骤 5: 整合输出智能体生成最终回答
        final_answer = await self.reply_agent.generate_reply(
            question=query,
            chunks=chunks if chunks else None,
            debate_result=debate_result,
            judgment_result=judgment_result,
            session_id=session_id,
            user_id=user_id
        )
        
        # 构建返回结果
        result = {
            "question": query,
            "answer": final_answer,
            "sources": chunks,
            "num_sources": len(chunks),
            "session_id": session_id,
            "processing_path": plan.processing_path.value,
            "plan": plan.dict()
        }
        
        if debate_result:
            result["debate_result"] = debate_result
        if judgment_result:
            result["judgment_result"] = judgment_result.to_dict()
        
        return result
    
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
        # 使用 Workflow 执行
        # 根据 Agno 文档，使用 input 参数传递主要数据，additional_data 传递额外数据
        # session_id 和 user_id 是标准参数，用于会话管理
        result = await self.workflow.arun(
            input={"query": question, "question": question},  # 使用标准的 input 参数
            additional_data={"session_id": session_id, "user_id": user_id},  # 额外数据
            session_id=session_id,  # 标准参数，用于会话管理
            user_id=user_id  # 标准参数，用于用户标识
        )
        
        # 从 Workflow 结果中提取内容
        if hasattr(result, 'content'):
            return result.content
        elif isinstance(result, dict):
            return result
        else:
            return {
                "question": question,
                "answer": str(result),
                "sources": [],
                "num_sources": 0,
                "session_id": session_id
            }

