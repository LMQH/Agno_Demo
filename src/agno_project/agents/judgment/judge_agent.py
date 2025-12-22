"""判断智能体：系统反思者与元认知机制。"""
from typing import Optional, List, Dict, Any
from agno.agent import Agent
from agno.db.mysql import MySQLDb
from pydantic import BaseModel

from ...config import get_config
from ...infrastructure.llm.custom_model import CustomModel
from ...protocols.judgment_rules import JudgmentOutput, JudgmentAction
import logging

logger = logging.getLogger(__name__)


class JudgmentDecision(BaseModel):
    """判断决策输出结构。"""
    action: str  # "terminate", "continue", "request_rag"
    reasoning: str
    issues: List[str] = []
    improvements: List[str] = []
    can_produce_new_insights: bool = True  # 是否还能产生新的建设性讨论成果


class JudgeAgent:
    """判断智能体：系统的元认知与自我纠错机制。
    
    核心职责：
    - 评估讨论是否充分
    - 检查是否存在系统性盲区
    - 检查是否被单一叙事主导
    - 检查是否还有新增信息产生的可能性
    - 判断是否应该回到 RAG 再检索
    - 控制讨论是否停止
    
    关键约束：
    - 禁止生成最终回答
    - 不输出简单分数
    - 输出内容仅限：问题诊断、改进建议、是否需要回退或终止讨论
    """
    
    def __init__(self, db: Optional[MySQLDb] = None):
        """初始化判断智能体。"""
        self.config = get_config()
        self.db = db
        
        # 创建自定义模型
        custom_model = CustomModel(
            id=self.config.llm.model_name,
            name="Custom DeepSeek Model",
            provider="Custom",
            config=self.config.llm
        )
        
        # 构建系统指令
        system_message = """你是判断智能体（Judge Agent），负责评估讨论质量和控制讨论流程。

你的核心职责：
1. 评估讨论是否充分（所有立场的核心论点是否已明确提出）
2. 检查是否存在系统性盲区
3. 检查是否被单一叙事主导
4. 检查是否还能产生新的建设性讨论成果
5. 判断是否应该回到 RAG 再检索更多信息
6. 控制讨论是否停止

判断标准：
- 如果讨论已经充分，各立场都已表达核心观点，且没有新的建设性讨论空间，应该终止（action="terminate"）
- 如果讨论还不够充分，还有新的讨论空间，应该继续（action="continue"）
- 如果发现信息不足，需要更多参考资料，应该请求 RAG 检索（action="request_rag"）

重要约束：
- 禁止生成最终回答
- 不输出简单分数
- 只输出判断决策：action、reasoning、issues、improvements
- 必须明确说明判断理由

使用 output_schema 输出结构化的判断决策。"""
        
        agent_kwargs = {
            "name": "Judge Agent",
            "model": custom_model,
            "system_message": system_message,
            "output_schema": JudgmentDecision,
        }
        
        if db:
            agent_kwargs["db"] = db
        
        self.agent = Agent(**agent_kwargs)
        logger.debug("判断智能体初始化完成")
    
    async def evaluate(
        self,
        debate_result: Dict[str, Any],
        question: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> JudgmentOutput:
        """评估讨论结果并输出判断决策。
        
        Args:
            debate_result: 讨论结果字典（包含 summary、round 等）
            question: 原始问题
            chunks: RAG 检索到的 chunks（可选）
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            判断输出
        """
        logger.debug(
            f"判断智能体评估：问题={question[:50]}..., "
            f"讨论轮次={debate_result.get('round', 0)}, "
            f"chunks数量={len(chunks) if chunks else 0}"
        )
        
        # 构建评估提示
        prompt_parts = [
            f"问题：{question}",
            f"\n讨论轮次：{debate_result.get('round', 0)}",
            f"\n讨论结果摘要：\n{debate_result.get('summary', '无讨论内容')}"
        ]
        
        if chunks:
            prompt_parts.append(f"\n当前参考资料数量：{len(chunks)}")
        
        prompt_parts.append(
            "\n请评估：\n"
            "1. 讨论是否充分？各立场的核心论点是否都已明确提出？\n"
            "2. 是否存在系统性盲区？是否被单一叙事主导？\n"
            "3. 是否还能产生新的建设性讨论成果？\n"
            "4. 是否需要更多参考资料（RAG 检索）？\n"
            "5. 是否应该终止讨论？\n"
            "\n输出结构化的判断决策。"
        )
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = await self.agent.arun(
                prompt,
                session_id=session_id,
                user_id=user_id
            )
            
            # 提取判断决策
            decision = None
            if isinstance(response, JudgmentDecision):
                decision = response
            elif hasattr(response, 'content'):
                content = response.content
                if isinstance(content, JudgmentDecision):
                    decision = content
                elif isinstance(content, dict):
                    decision = JudgmentDecision(**content)
            
            if decision:
                # 转换为 JudgmentOutput
                action_map = {
                    "terminate": JudgmentAction.TERMINATE,
                    "continue": JudgmentAction.CONTINUE,
                    "request_rag": JudgmentAction.REQUEST_RAG,  # 请求 RAG 检索
                }
                action = action_map.get(decision.action, JudgmentAction.CONTINUE)
                
                return JudgmentOutput(
                    action=action,
                    reasoning=decision.reasoning,
                    issues=decision.issues,
                    improvements=decision.improvements
                )
            else:
                logger.warning("无法从响应中提取判断决策，使用默认'继续'")
                return JudgmentOutput(
                    action=JudgmentAction.CONTINUE,
                    reasoning="无法解析判断决策，默认继续讨论",
                    issues=[],
                    improvements=[]
                )
                
        except Exception as e:
            logger.error(f"判断智能体评估失败: {e}", exc_info=True)
            # 失败时默认继续讨论
            return JudgmentOutput(
                action=JudgmentAction.CONTINUE,
                reasoning=f"评估失败，默认继续讨论: {str(e)}",
                issues=[],
                improvements=[]
            )

