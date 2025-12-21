"""Planner Agent 输出结构定义。"""
from pydantic import BaseModel
from typing import Literal, Optional, List
from enum import Enum


class ProcessingPath(str, Enum):
    """处理路径枚举。"""
    DIRECT_TOOL = "direct_tool"  # 直接工具执行
    MULTI_AGENT_DEBATE = "multi_agent_debate"  # 进入多智能体讨论
    DEGRADED_ANALYSIS = "degraded_analysis"  # 降级处理
    REJECT = "reject"  # 拒绝处理


class RiskLevel(str, Enum):
    """风险等级枚举。"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplexityLevel(str, Enum):
    """复杂度等级枚举。"""
    SIMPLE = "simple"  # 简单问题，可直接回答
    MODERATE = "moderate"  # 中等复杂度，需要检索
    COMPLEX = "complex"  # 复杂问题，存在立场冲突
    VERY_COMPLEX = "very_complex"  # 高度复杂，需要多立场讨论


class PlanOutput(BaseModel):
    """Planner Agent 的输出结构。"""
    processing_path: ProcessingPath
    complexity_level: ComplexityLevel
    risk_level: RiskLevel
    reasoning: str  # 决策理由，必须解释为什么选择这个路径
    requires_retrieval: bool = True  # 是否需要检索知识库
    allowed_agents: Optional[List[str]] = None  # 允许参与讨论的 Agent 列表（如果进入讨论）
    max_debate_rounds: Optional[int] = None  # 最大讨论轮次（如果进入讨论）
    restrictions: Optional[List[str]] = None  # 处理限制（如：禁止推测、禁止站队等）

