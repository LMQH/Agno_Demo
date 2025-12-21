"""讨论回合控制协议。"""
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
from enum import Enum


class DebateStatus(str, Enum):
    """讨论状态枚举。"""
    ONGOING = "ongoing"  # 进行中
    TERMINATED = "terminated"  # 已终止
    COMPLETED = "completed"  # 已完成


class TerminationReason(str, Enum):
    """终止原因枚举。"""
    ALL_ARGUMENTS_PRESENTED = "all_arguments_presented"  # 所有立场论点已提出
    NO_NEW_INFORMATION = "no_new_information"  # 未引入新事实或新视角
    DIVERGENCE_STRUCTURED = "divergence_structured"  # 分歧已清晰结构化
    MAX_ROUNDS_REACHED = "max_rounds_reached"  # 达到最大轮次
    EVAL_RECOMMENDATION = "eval_recommendation"  # Eval Agent 建议终止


class DebateRound(BaseModel):
    """讨论轮次信息。"""
    round_number: int
    agent_name: str
    content: str
    responds_to: Optional[str] = None  # 回应哪个 Agent


class DebateState(BaseModel):
    """讨论状态。"""
    status: DebateStatus
    current_round: int
    max_rounds: int
    participants: List[str]  # 参与讨论的 Agent 列表
    rounds: List[DebateRound]  # 讨论轮次历史
    termination_reason: Optional[TerminationReason] = None
    new_information_count: int = 0  # 本轮引入的新信息数量


class DebateProtocol:
    """讨论协议管理器。"""
    
    @staticmethod
    def should_terminate(
        state: DebateState,
        eval_recommendation: Optional[str] = None
    ) -> Tuple[bool, Optional[TerminationReason]]:
        """判断是否应该终止讨论。
        
        Args:
            state: 当前讨论状态
            eval_recommendation: Eval Agent 的建议
        
        Returns:
            (是否终止, 终止原因)
        """
        # 硬性回合上限
        if state.current_round >= state.max_rounds:
            return True, TerminationReason.MAX_ROUNDS_REACHED
        
        # Eval Agent 建议终止
        if eval_recommendation and "terminate" in eval_recommendation.lower():
            return True, TerminationReason.EVAL_RECOMMENDATION
        
        # TODO: 实现其他终止条件判断逻辑
        # - 所有立场的核心论点已明确提出
        # - 新一轮讨论未引入新事实或新视角
        # - 分歧已被清晰结构化
        
        return False, None
    
    @staticmethod
    def get_next_speaker(
        state: DebateState,
        allowed_agents: Optional[List[str]] = None
    ) -> Optional[str]:
        """获取下一个发言的 Agent。
        
        Args:
            state: 当前讨论状态
            allowed_agents: 允许发言的 Agent 列表
        
        Returns:
            下一个发言的 Agent 名称，如果无则返回 None
        """
        # TODO: 实现发言顺序逻辑
        # 可以基于轮次、上次发言者等来决定
        if not allowed_agents:
            allowed_agents = state.participants
        
        if not allowed_agents:
            return None
        
        # 简单轮换逻辑
        round_index = state.current_round % len(allowed_agents)
        return allowed_agents[round_index]

