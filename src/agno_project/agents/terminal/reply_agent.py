"""Reply Agent：裁决与整合者。"""
from typing import Optional, List, Dict, Any
from agno.agent import Agent
from agno.db.mysql import MySQLDb

from ...config import get_config
from ...infrastructure.llm.custom_model import CustomModel
from ...protocols.debate_protocol import DebateState
import logging

logger = logging.getLogger(__name__)


class ReplyAgent:
    """Reply Agent：最终对用户负责的结构化裁决者。
    
    核心职责：
    - 整合多 Agent 的结果
    - 明确区分：事实共识、立场分歧、不确定性与未来变量
    - 避免制造"虚假中立"
    
    关键约束：
    - 不站队
    - 不抹平分歧
    - 明确告诉用户哪些结论依赖立场假设
    """
    
    def __init__(self, db: Optional[MySQLDb] = None):
        """初始化 Reply Agent。"""
        self.config = get_config()
        
        # 创建自定义模型
        custom_model = CustomModel(
            id=self.config.llm.model_name,
            name="Custom DeepSeek Model",
            provider="Custom",
            config=self.config.llm
        )
        
        # 构建系统指令
        system_message = """你是 Reply Agent（裁决与整合者），负责整合多 Agent 的讨论结果并生成最终回答。

你的核心职责：
1. 整合多 Agent 的讨论结果
2. 明确区分：
   - 事实共识：各方都认可的事实
   - 立场分歧：不同立场之间的观点差异
   - 不确定性与未来变量：无法确定或需要未来验证的部分
3. 结构化呈现结果

重要约束：
- 不站队：不偏向任何一方立场
- 不抹平分歧：明确呈现不同立场之间的分歧
- 明确告诉用户哪些结论依赖立场假设
- 避免制造"虚假中立"（看似中立实则模糊）
- 基于知识库内容，引用具体事实

输出格式建议：
1. 事实共识
2. 立场分歧（分别列出各立场的核心观点）
3. 不确定性与未来变量
4. 参考来源"""
        
        agent_kwargs = {
            "name": "Reply Agent",
            "model": custom_model,
            "system_message": system_message,
        }
        
        if db:
            agent_kwargs["db"] = db
        
        self.agent = Agent(**agent_kwargs)
        logger.info("Reply Agent 初始化完成")
    
    async def generate_reply(
        self,
        question: str,
        debate_state: Optional[DebateState] = None,
        direct_response: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """生成最终回答。
        
        Args:
            question: 原始问题
            debate_state: 讨论状态（如果进行了多 Agent 讨论）
            direct_response: 直接响应（如果是直接工具执行）
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            最终回答
        """
        if direct_response:
            # 如果是直接响应，只需要简单整合
            prompt = f"""问题：{question}

直接响应结果：{direct_response}

请基于上述结果，生成结构化的最终回答。"""
        elif debate_state:
            # 如果有讨论状态，需要整合各立场观点
            rounds_summary = []
            for round_info in debate_state.rounds:
                rounds_summary.append(f"{round_info.agent_name}：{round_info.content}")
            
            prompt = f"""问题：{question}

多 Agent 讨论结果：
{chr(10).join(rounds_summary) if rounds_summary else '无讨论内容'}

请整合上述讨论结果，生成结构化的最终回答。明确区分：
1. 事实共识
2. 立场分歧（分别列出各立场的核心观点）
3. 不确定性与未来变量"""
        else:
            # 没有讨论也没有直接响应（不应该发生）
            logger.warning("Reply Agent 收到空输入")
            return "无法生成回答：缺少必要的输入信息"
        
        try:
            response = await self.agent.arun(
                prompt,
                session_id=session_id,
                user_id=user_id
            )
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
        except Exception as e:
            logger.error(f"Reply Agent 生成回答失败: {e}", exc_info=True)
            return f"生成最终回答失败: {str(e)}"

