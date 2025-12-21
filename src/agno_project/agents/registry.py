"""Agent 注册与发现机制。"""
from typing import Dict, Type, Optional, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 基础接口。"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称。"""
        pass


class AgentRegistry:
    """Agent 注册表。"""
    
    _registry: Dict[str, Type[BaseAgent]] = {}
    
    @classmethod
    def register(cls, name: str, agent_class: Type[BaseAgent]) -> None:
        """注册 Agent。
        
        Args:
            name: Agent 名称
            agent_class: Agent 类
        """
        if name in cls._registry:
            logger.warning(f"Agent '{name}' 已注册，将被覆盖")
        cls._registry[name] = agent_class
        logger.info(f"已注册 Agent: {name}")
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseAgent]]:
        """获取已注册的 Agent 类。
        
        Args:
            name: Agent 名称
        
        Returns:
            Agent 类，如果不存在则返回 None
        """
        return cls._registry.get(name)
    
    @classmethod
    def list_all(cls) -> List[str]:
        """列出所有已注册的 Agent 名称。
        
        Returns:
            Agent 名称列表
        """
        return list(cls._registry.keys())
    
    @classmethod
    def clear(cls) -> None:
        """清空注册表。"""
        cls._registry.clear()
        logger.info("Agent 注册表已清空")


# 注册所有 Agent（在导入时自动注册）
def register_agents():
    """注册所有 Agent。"""
    from .planning.planner_agent import PlannerAgent
    from .capability.rag_agent import RAGAgent
    from .debate.conservative_agent import ConservativeAgent
    from .debate.radical_agent import RadicalAgent
    from .debate.official_agent import OfficialAgent
    from .judgment.judge_agent import JudgeAgent
    from .terminal.reply_agent import ReplyAgent
    
    AgentRegistry.register("planner", PlannerAgent)
    AgentRegistry.register("rag", RAGAgent)
    AgentRegistry.register("conservative", ConservativeAgent)
    AgentRegistry.register("radical", RadicalAgent)
    AgentRegistry.register("official", OfficialAgent)
    AgentRegistry.register("judge", JudgeAgent)
    AgentRegistry.register("reply", ReplyAgent)


# 自动注册
try:
    register_agents()
except Exception as e:
    logger.warning(f"Agent 自动注册失败: {e}")

