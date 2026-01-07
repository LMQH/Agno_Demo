"""讨论团队 Leader Agent：负责协调队员和控制讨论节奏。"""
from typing import Optional
from agno.agent import Agent
from agno.db.mysql import MySQLDb

from ...config import get_config
from ...infrastructure.llm.custom_model import CustomModel
import logging

logger = logging.getLogger(__name__)


class LeaderAgent:
    """讨论团队 Leader Agent：负责协调队员和控制讨论节奏。
    
    核心职责：
    - 协调队员（激进派、保守派、官方叙事）进行讨论
    - 控制讨论节奏，确保每个立场都有机会表达观点
    - 引导队员针对问题进行深入讨论
    - 整合讨论结果，形成阶段性讨论总结
    """
    
    def __init__(
        self,
        db: Optional[MySQLDb] = None
    ):
        """初始化 Leader Agent。"""
        self.config = get_config()
        
        # 创建自定义模型
        custom_model = CustomModel(
            id=self.config.llm.model_name,
            name="Custom DeepSeek Model",
            provider="Custom",
            config=self.config.llm
        )
        
        # 构建系统指令
        system_message = """你是讨论团队的 Leader，负责协调队员和控制讨论节奏。

你的职责：
1. 协调队员（激进派、保守派、官方叙事）进行讨论
2. 控制讨论节奏，确保每个立场都有机会表达观点
3. 引导队员针对问题进行深入讨论
4. 整合讨论结果，形成阶段性讨论总结

重要约束：
- 不参与观点生成，只负责协调
- 确保讨论有序进行
- 及时总结讨论要点
- 控制讨论时间，避免无意义的重复"""
        
        agent_kwargs = {
            "name": "Debate Leader",
            "model": custom_model,
            "system_message": system_message,
        }
        
        if db:
            agent_kwargs["db"] = db
        
        self.agent = Agent(**agent_kwargs)
        logger.debug("Leader Agent 初始化完成")

