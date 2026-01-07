"""PlannerAgent：治理与分流中枢。"""
from typing import Optional, Dict, Any
from agno.agent import Agent
from agno.db.mysql import MySQLDb
from pydantic import BaseModel
import json

from ...config import get_config
from ...infrastructure.llm.custom_model import CustomModel
from ...protocols.plan_schema import PlanOutput, ProcessingPath, RiskLevel, ComplexityLevel
from ...protocols.safety_policy import SafetyPolicy, SafetyAction
from ...tools.rag_retrieval_tool import RAGRetrievalTool
from ...infrastructure.database.retriever import RAGRetriever
import logging

logger = logging.getLogger(__name__)


def _parse_plan_output(response: Any) -> Optional[PlanOutput]:
    """从 Agent 响应中解析 PlanOutput。
    
    Agno Agent 使用 output_schema 时，响应可能有多种格式：
    1. 直接是 PlanOutput 实例
    2. 响应对象有 content 属性，content 可能是 PlanOutput、dict 或 JSON 字符串
    3. 响应对象有其他属性包含解析后的对象
    
    Args:
        response: Agent 的响应对象
        
    Returns:
        解析后的 PlanOutput，如果解析失败则返回 None
    """
    # 方式1: 如果 response 直接是 PlanOutput 实例
    if isinstance(response, PlanOutput):
        logger.debug("响应直接是 PlanOutput 实例")
        return response
    
    # 方式2: 如果通过 content 属性访问
    if hasattr(response, 'content'):
        content = response.content
        logger.debug(f"从 content 属性解析，content 类型: {type(content)}")
        
        # content 是 PlanOutput 实例
        if isinstance(content, PlanOutput):
            return content
        
        # content 是字典，尝试转换为 PlanOutput
        if isinstance(content, dict):
            try:
                # 确保枚举字段正确转换
                plan_dict = _normalize_plan_dict(content)
                return PlanOutput(**plan_dict)
            except Exception as e:
                logger.warning(f"无法将 content 字典转换为 PlanOutput: {e}, 字典内容: {content}")
                return None
        
        # content 是字符串，可能是 JSON
        if isinstance(content, str):
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    plan_dict = _normalize_plan_dict(data)
                    return PlanOutput(**plan_dict)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"无法解析 content 字符串为 JSON: {e}, 字符串内容: {content[:200]}")
                return None
    
    # 方式3: 检查其他可能的属性（如 parsed_output, output 等）
    for attr_name in ['parsed_output', 'output', 'result', 'data']:
        if hasattr(response, attr_name):
            attr_value = getattr(response, attr_name)
            if isinstance(attr_value, PlanOutput):
                logger.debug(f"从 {attr_name} 属性找到 PlanOutput")
                return attr_value
            elif isinstance(attr_value, dict):
                try:
                    plan_dict = _normalize_plan_dict(attr_value)
                    return PlanOutput(**plan_dict)
                except Exception as e:
                    logger.debug(f"无法从 {attr_name} 属性转换为 PlanOutput: {e}")
    
    # 方式4: 如果 response 本身就是字典
    if isinstance(response, dict):
        try:
            plan_dict = _normalize_plan_dict(response)
            return PlanOutput(**plan_dict)
        except Exception as e:
            logger.warning(f"无法将响应字典转换为 PlanOutput: {e}, 字典内容: {response}")
            return None
    
    logger.warning(f"无法从响应中提取 PlanOutput，响应类型: {type(response)}")
    return None


def _normalize_plan_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """规范化 PlanOutput 字典，确保枚举字段正确转换。
    
    Args:
        data: 原始的字典数据
        
    Returns:
        规范化后的字典
    """
    normalized = data.copy()
    
    # 处理 processing_path 枚举
    if 'processing_path' in normalized:
        path_value = normalized['processing_path']
        if not isinstance(path_value, ProcessingPath):
            if isinstance(path_value, str):
                try:
                    normalized['processing_path'] = ProcessingPath(path_value)
                except ValueError:
                    # 尝试匹配（忽略大小写）
                    path_value_lower = path_value.lower()
                    for path in ProcessingPath:
                        if path.value.lower() == path_value_lower:
                            normalized['processing_path'] = path
                            break
                    else:
                        logger.warning(f"无法识别的 processing_path 值: {path_value}，使用默认值 DIRECT_TOOL")
                        normalized['processing_path'] = ProcessingPath.DIRECT_TOOL
    
    # 处理 complexity_level 枚举
    if 'complexity_level' in normalized:
        complexity_value = normalized['complexity_level']
        if not isinstance(complexity_value, ComplexityLevel):
            if isinstance(complexity_value, str):
                try:
                    normalized['complexity_level'] = ComplexityLevel(complexity_value)
                except ValueError:
                    complexity_value_lower = complexity_value.lower()
                    for level in ComplexityLevel:
                        if level.value.lower() == complexity_value_lower:
                            normalized['complexity_level'] = level
                            break
                    else:
                        logger.warning(f"无法识别的 complexity_level 值: {complexity_value}，使用默认值 MODERATE")
                        normalized['complexity_level'] = ComplexityLevel.MODERATE
    
    # 处理 risk_level 枚举
    if 'risk_level' in normalized:
        risk_value = normalized['risk_level']
        if not isinstance(risk_value, RiskLevel):
            if isinstance(risk_value, str):
                try:
                    normalized['risk_level'] = RiskLevel(risk_value)
                except ValueError:
                    risk_value_lower = risk_value.lower()
                    for level in RiskLevel:
                        if level.value.lower() == risk_value_lower:
                            normalized['risk_level'] = level
                            break
                    else:
                        logger.warning(f"无法识别的 risk_level 值: {risk_value}，使用默认值 LOW")
                        normalized['risk_level'] = RiskLevel.LOW
    
    return normalized


class PlannerAgent:
    """Router Agent：判断问题复杂度、风险等级，决定处理路径。
    
    核心职责：
    - 判断问题复杂度（是否存在立场冲突、意识形态对立）
    - 判断风险等级（是否高度敏感、是否可能诱导极端行为）
    - 决定处理路径：直接工具执行 / 进入多智能体讨论 / 降级处理 / 拒绝处理
    
    关键约束：
    - 不参与观点生成
    - 必须解释决策理由
    - 只决定"谁来处理、如何处理"，不决定"结论是什么"
    """
    
    def __init__(
        self,
        db: Optional[MySQLDb] = None,
        retriever: Optional[RAGRetriever] = None
    ):
        """初始化 Router Agent。"""
        self.config = get_config()
        self.db = db
        
        # 创建自定义模型
        custom_model = CustomModel(
            id=self.config.llm.model_name,
            name="Custom DeepSeek Model",
            provider="Custom",
            config=self.config.llm
        )
        
        # 创建工具（可能需要检索来判断问题）
        rag_tool = RAGRetrievalTool(retriever=retriever) if retriever else None
        
        # 构建系统指令
        system_message = """你是 Router Agent，是整个系统的治理与决策中枢。

你的职责：
1. 分析用户问题的复杂度和风险等级
2. 决定处理路径（直接工具执行 / 多智能体讨论 / 降级处理 / 拒绝处理）
3. 解释决策理由

重要约束：
- 你不参与观点生成
- 你必须解释每个决策的理由
- 你只决定"谁来处理、如何处理"，不决定"结论是什么"

处理路径说明：
- direct_tool: 简单问题，可直接使用工具（如 RAG 检索）回答
- multi_agent_debate: 复杂问题，存在立场冲突，需要多智能体讨论
- degraded_analysis: 高风险问题，需要降级为描述性分析
- reject: 违反安全策略，必须拒绝

使用 output_schema 输出结构化的决策结果。"""
        
        agent_kwargs = {
            "name": "Router Agent",
            "model": custom_model,
            "system_message": system_message,
            "output_schema": PlanOutput,
        }
        
        if rag_tool:
            agent_kwargs["tools"] = [rag_tool]
        
        if db:
            agent_kwargs["db"] = db
        
        self.agent = Agent(**agent_kwargs)
        logger.debug("Router Agent 初始化完成")
    
    async def plan(
        self,
        question: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> PlanOutput:
        """分析问题并制定处理计划。
        
        Args:
            question: 用户问题
            session_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            处理计划
        """
        # 首先进行安全检查
        safety_action, violation_type, safety_reason = SafetyPolicy.check_content(question)
        
        if safety_action == SafetyAction.REJECT:
            # 直接拒绝
            return PlanOutput(
                processing_path=ProcessingPath.REJECT,
                complexity_level=ComplexityLevel.SIMPLE,
                risk_level=RiskLevel.CRITICAL,
                reasoning=f"违反安全策略：{safety_reason}（违规类型：{violation_type.value if violation_type else 'unknown'}）",
                requires_retrieval=False
            )
        
        if SafetyPolicy.should_degrade(question):
            # 降级处理
            return PlanOutput(
                processing_path=ProcessingPath.DEGRADED_ANALYSIS,
                complexity_level=ComplexityLevel.COMPLEX,
                risk_level=RiskLevel.HIGH,
                reasoning="问题涉及规范性判断（应该/必须），需要降级为描述性分析",
                requires_retrieval=True,
                restrictions=["禁止给出'应该/必须'式结论", "转为描述性分析"]
            )
        
        # 使用 Agent 进行复杂度和风险分析
        prompt = f"""分析以下问题的复杂度和风险等级，并决定处理路径：

问题：{question}

请分析：
1. 问题复杂度：是否存在立场冲突、意识形态对立？
2. 风险等级：是否高度敏感、是否可能诱导极端行为？
3. 处理路径：应该选择哪个处理路径？

输出结构化的决策结果。"""
        
        try:
            response = await self.agent.arun(
                prompt,
                session_id=session_id,
                user_id=user_id
            )
            
            # 使用统一的解析函数提取 PlanOutput
            plan_output = _parse_plan_output(response)
            
            # 如果成功解析，返回结果
            if plan_output:
                logger.info(
                    f"Router Agent 决策成功: path={plan_output.processing_path.value}, "
                    f"complexity={plan_output.complexity_level.value}, "
                    f"risk={plan_output.risk_level.value}, "
                    f"reasoning={plan_output.reasoning[:100]}..."
                )
                return plan_output
            
            # 如果解析失败，记录详细信息并使用默认值
            logger.warning(
                f"无法从响应中提取 PlanOutput，响应类型: {type(response)}, "
                f"响应内容: {str(response)[:500]}"
            )
            # 如果响应有更多属性，记录它们以便调试
            if hasattr(response, '__dict__'):
                logger.debug(f"响应对象属性: {list(response.__dict__.keys())}")
            
            return PlanOutput(
                processing_path=ProcessingPath.DIRECT_TOOL,
                complexity_level=ComplexityLevel.MODERATE,
                risk_level=RiskLevel.LOW,
                reasoning="无法解析 Agent 响应，使用默认路径（直接工具执行）",
                requires_retrieval=True
            )
        except Exception as e:
            logger.error(f"Router Agent 规划失败: {e}", exc_info=True)
            # 失败时默认使用直接工具执行
            return PlanOutput(
                processing_path=ProcessingPath.DIRECT_TOOL,
                complexity_level=ComplexityLevel.MODERATE,
                risk_level=RiskLevel.LOW,
                reasoning=f"规划过程发生异常，使用默认路径: {str(e)}",
                requires_retrieval=True
            )

