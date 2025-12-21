"""Eval Agent：系统反思者与元认知机制。"""
from typing import Optional, List, Dict, Any
from agno.db.mysql import MySQLDb

from ...config import get_config
from ...protocols.judgment_rules import JudgmentOutput, JudgmentAction
from ...protocols.debate_protocol import DebateState
import logging

# 以下导入保留用于后续迭代中恢复完整实现
# from agno.agent import Agent
# from ...infrastructure.llm.custom_model import CustomModel

logger = logging.getLogger(__name__)


class JudgeAgent:
    """Eval Agent：系统的元认知与自我纠错机制。
    
    核心职责：
    - 评估讨论是否充分
    - 检查是否存在系统性盲区
    - 检查是否被单一叙事主导
    - 检查是否还有新增信息产生的可能性
    - 输出改进建议或终止建议
    
    关键约束：
    - 禁止生成最终回答
    - 不输出简单分数
    - 输出内容仅限：问题诊断、改进建议、是否需要回退或终止讨论
    """
    
    def __init__(self, db: Optional[MySQLDb] = None):
        """初始化 Eval Agent。
        
        Args:
            db: 数据库连接（当前简化版本未使用，保留用于后续迭代）
        
        Note:
            当前为简化版本，不创建 Agent 实例。
            后续迭代中恢复完整实现时，将重新启用 Agent 初始化。
        """
        self.config = get_config()
        self.db = db
        
        # TODO: 后续迭代中恢复 Agent 初始化
        # 当前简化版本直接返回默认响应，不需要调用 LLM
        # self.agent = Agent(...)
        
        logger.info("Eval Agent 初始化完成（简化版本：直接返回默认'继续'响应）")
    
    async def evaluate(
        self,
        debate_state: DebateState,
        question: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> JudgmentOutput:
        """评估讨论状态并输出判断结果。
        
        Args:
            debate_state: 当前讨论状态
            question: 原始问题
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            判断输出（当前为简化版本，直接返回"继续"）
        
        Note:
            当前为简化实现，直接返回默认"继续"响应。
            复杂的判断逻辑将在后续迭代中完善。
        """
        # TODO: 后续迭代中实现完整的评估逻辑
        # 包括：
        # 1. 评估讨论是否充分（所有立场的核心论点是否已明确提出）
        # 2. 检查是否存在系统性盲区
        # 3. 检查是否被单一叙事主导
        # 4. 检查是否还有新增信息产生的可能性
        
        logger.debug(
            f"Eval Agent 评估（简化版）：讨论状态={debate_state.status.value}, "
            f"当前轮次={debate_state.current_round}/{debate_state.max_rounds}"
        )
        
        # 直接返回默认"继续"响应
        return JudgmentOutput(
            action=JudgmentAction.CONTINUE,
            reasoning="简化版本：默认允许继续讨论（复杂判断逻辑将在后续迭代中完善）",
            issues=[],
            improvements=[]
        )

