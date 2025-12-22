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
        logger.debug("Reply Agent 初始化完成")
    
    async def generate_reply(
        self,
        question: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        debate_result: Optional[Dict[str, Any]] = None,
        judgment_result: Optional[Any] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """生成最终回答。
        
        Args:
            question: 原始问题
            chunks: RAG 检索到的 chunks（可选）
            debate_result: 讨论结果（可选，如果进行了讨论）
            judgment_result: 判断结果（可选）
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            最终回答
        """
        # 构建提示
        prompt_parts = [f"问题：{question}"]
        
        # 添加 chunks（如果有）
        if chunks:
            chunks_text = "\n\n".join([
                f"来源：{chunk.get('file_name', '未知')}\n内容：{chunk.get('content', '')}"
                for chunk in chunks[:10]  # 最多取前 10 个
            ])
            prompt_parts.append(f"\n参考资料：\n{chunks_text}")
        
        # 添加讨论结果（如果有）
        if debate_result:
            prompt_parts.append(
                f"\n讨论团队讨论结果（轮次 {debate_result.get('round', 0)}）：\n"
                f"{debate_result.get('summary', '无讨论内容')}"
            )
        
        # 添加判断结果（如果有）
        if judgment_result:
            prompt_parts.append(
                f"\n判断智能体评审意见：\n"
                f"动作：{judgment_result.action.value}\n"
                f"理由：{judgment_result.reasoning}"
            )
            if judgment_result.issues:
                prompt_parts.append(f"发现的问题：\n" + "\n".join(f"- {issue}" for issue in judgment_result.issues))
            if judgment_result.improvements:
                prompt_parts.append(f"改进建议：\n" + "\n".join(f"- {improvement}" for improvement in judgment_result.improvements))
        
        # 根据输入情况构建不同的提示
        if debate_result:
            # 有讨论结果，需要整合各立场观点
            prompt_parts.append(
                "\n请整合上述信息，生成结构化的最终回答。明确区分：\n"
                "1. 事实共识（各方都认可的事实）\n"
                "2. 立场分歧（分别列出各立场的核心观点）\n"
                "3. 不确定性与未来变量（无法确定或需要未来验证的部分）\n"
                "4. 参考来源（引用具体的参考资料）"
            )
        elif chunks:
            # 只有 chunks，基于参考资料回答
            prompt_parts.append(
                "\n请基于上述参考资料，生成结构化的最终回答。"
            )
        else:
            # 只有问题，直接回答
            prompt_parts.append(
                "\n请基于你的知识，生成结构化的最终回答。"
            )
        
        prompt = "\n".join(prompt_parts)
        
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

