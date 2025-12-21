"""安全策略定义。"""
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import re


class SafetyViolationType(str, Enum):
    """安全违规类型枚举。"""
    VIOLENCE_INCITEMENT = "violence_incitement"  # 煽动暴力
    HATE_SPEECH = "hate_speech"  # 仇恨言论
    TARGETED_ATTACK = "targeted_attack"  # 针对特定群体/国家的攻击
    VIOLENCE_JUSTIFICATION = "violence_justification"  # 为暴力行为正当化
    EXTREMIST_MOBILIZATION = "extremist_mobilization"  # 极端动员


class SafetyAction(str, Enum):
    """安全动作枚举。"""
    REJECT = "reject"  # 直接拒绝
    DEGRADE = "degrade"  # 降级处理
    RESTRICT = "restrict"  # 限制处理范围
    ALLOW = "allow"  # 允许处理


class SafetyPolicy:
    """安全策略管理器。"""
    
    # 危险关键词列表（简化版本，仅作为demo示例，后续会完善）
    VIOLENCE_KEYWORDS = [
        "清洗",
    ]
    
    # 仇恨言论模式（简化版本，仅作为demo示例，后续会完善）
    HATE_SPEECH_PATTERNS = [
        r".*该死",
    ]
    
    @staticmethod
    def check_content(content: str) -> Tuple[SafetyAction, Optional[SafetyViolationType], str]:
        """检查内容是否违反安全策略。
        
        Args:
            content: 要检查的内容
        
        Returns:
            (动作, 违规类型, 理由)
        """
        content_lower = content.lower()
        
        # 检查暴力煽动
        for keyword in SafetyPolicy.VIOLENCE_KEYWORDS:
            if keyword.lower() in content_lower:
                # 进一步检查是否为动员性话语
                if SafetyPolicy._is_mobilization_language(content, keyword):
                    return (
                        SafetyAction.REJECT,
                        SafetyViolationType.VIOLENCE_INCITEMENT,
                        f"检测到暴力煽动关键词: {keyword}"
                    )
        
        # 检查仇恨言论模式
        for pattern in SafetyPolicy.HATE_SPEECH_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return (
                    SafetyAction.REJECT,
                    SafetyViolationType.HATE_SPEECH,
                    f"检测到仇恨言论模式: {pattern}"
                )
        
        # 简化版本：仅做基本检查，后续会完善
        
        return SafetyAction.ALLOW, None, "内容通过安全检查"
    
    @staticmethod
    def _is_mobilization_language(content: str, keyword: str) -> bool:
        """判断是否为动员性话语（而非分析性讨论）。
        
        Args:
            content: 内容
            keyword: 关键词
        
        Returns:
            是否为动员性话语
        """
        # 简化版本：检测到关键词即认为是动员性话语
        # 后续会完善更精确的判断逻辑
        return True
    
    @staticmethod
    def should_degrade(question: str) -> bool:
        """判断问题是否应该降级处理。
        
        降级处理的问题类型：
        - 要求做出"应该/必须"式结论的问题
        
        Args:
            question: 用户问题
        
        Returns:
            是否应该降级处理
        
        Note:
            当前为简化版本，暂不进行降级判断，后续会完善
        """
        # 简化版本：暂不进行降级判断，后续会完善
        return False
    
    @staticmethod
    def get_degraded_response_guidance() -> str:
        """获取降级处理的响应指导。"""
        return """对于此类问题，应转为描述性分析，而非规范性判断：
1. 描述各方立场和观点
2. 分析潜在风险和后果
3. 引用历史案例
4. 明确不确定性
禁止：
- 给出"应该/必须"式结论
- 支持或反对特定立场
- 进行推测性对抗"""

