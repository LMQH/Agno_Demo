"""判断/评估规则定义。"""
from typing import List, Dict, Any, Optional
from enum import Enum


class JudgmentAction(str, Enum):
    """判断动作枚举。"""
    CONTINUE = "continue"  # 继续讨论
    TERMINATE = "terminate"  # 终止讨论
    REQUEST_SPECIFIC_RESPONSE = "request_specific_response"  # 要求特定 Agent 回应
    ESCALATE = "escalate"  # 升级处理（如需要更多信息，包括请求 RAG 检索）
    REQUEST_RAG = "request_rag"  # 请求 RAG 检索更多信息


class JudgmentOutput:
    """Eval Agent 的输出结构。"""
    
    def __init__(
        self,
        action: JudgmentAction,
        reasoning: str,
        issues: Optional[List[str]] = None,
        improvements: Optional[List[str]] = None,
        requested_agent: Optional[str] = None,
        requested_topic: Optional[str] = None
    ):
        """初始化判断输出。
        
        Args:
            action: 建议的动作
            reasoning: 判断理由
            issues: 发现的问题列表
            improvements: 改进建议列表
            requested_agent: 如果 action 是 REQUEST_SPECIFIC_RESPONSE，指定请求的 Agent
            requested_topic: 如果 action 是 REQUEST_SPECIFIC_RESPONSE，指定请求回应的主题
        """
        self.action = action
        self.reasoning = reasoning
        self.issues = issues or []
        self.improvements = improvements or []
        self.requested_agent = requested_agent
        self.requested_topic = requested_topic
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "action": self.action.value,
            "reasoning": self.reasoning,
            "issues": self.issues,
            "improvements": self.improvements,
            "requested_agent": self.requested_agent,
            "requested_topic": self.requested_topic
        }


class JudgmentRules:
    """判断规则集合。"""
    
    @staticmethod
    def evaluate_debate_quality(
        rounds: List[Dict[str, Any]],
        participants: List[str]
    ) -> List[str]:
        """评估讨论质量，返回发现的问题列表。
        
        Args:
            rounds: 讨论轮次列表
            participants: 参与者列表
        
        Returns:
            问题列表
        """
        issues = []
        
        # TODO: 实现评估逻辑
        # - 检查讨论是否充分
        # - 检查是否存在系统性盲区
        # - 检查是否被单一叙事主导
        # - 检查是否还有新增信息产生的可能性
        
        return issues
    
    @staticmethod
    def check_argument_coverage(
        rounds: List[Dict[str, Any]],
        expected_positions: List[str]
    ) -> Dict[str, bool]:
        """检查论点覆盖情况。
        
        Args:
            rounds: 讨论轮次列表
            expected_positions: 期望的立场列表
        
        Returns:
            每个立场的覆盖情况（True 表示已覆盖）
        """
        coverage = {position: False for position in expected_positions}
        
        # TODO: 实现覆盖检查逻辑
        
        return coverage

