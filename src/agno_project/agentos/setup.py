"""
AgentOS 初始化模块：创建和配置 AgentOS 实例
"""
from agno.agent import Agent
from agno.db.mysql import MySQLDb
from agno.os import AgentOS
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.milvus import Milvus, SearchType
from agno.knowledge.embedder.openai import OpenAIEmbedder
import logging
import os

from ..config import get_config
from ..rag.custom_model import CustomModel

logger = logging.getLogger(__name__)

# 全局变量存储 AgentOS 实例
_agent_os: AgentOS = None
_agent_os_app = None


def create_agent_os() -> AgentOS:
    """
    创建并配置 AgentOS 实例。
    
    Returns:
        AgentOS 实例
    """
    global _agent_os
    
    if _agent_os is not None:
        logger.debug(f"AgentOS 已存在，直接返回现有实例")
        return _agent_os
    
    logger.info("开始创建 AgentOS 实例...")
    try:
        config = get_config()
        logger.debug("配置加载成功")
        
        # ========== LLM 模型配置 ==========
        llm_config = config.llm
        
        # 创建自定义模型实例（从配置文件读取）
        model = CustomModel(
            id=llm_config.model_name,
            name="Custom LLM Model",
            provider=llm_config.provider,
            config=llm_config
        )
        logger.info(f"✓ LLM 模型配置成功: {llm_config.model_name} ({llm_config.provider})")
        
        # ========== MySQL 配置 ==========
        mysql_config = config.mysql
        agent_db_config = config.agent_db
        
        # 构建 MySQL 连接字符串
        db_url = (
            f"mysql+pymysql://{mysql_config.user}:{mysql_config.password}"
            f"@{mysql_config.host}:{mysql_config.port}/{mysql_config.database}"
        )
        if mysql_config.charset:
            db_url += f"?charset={mysql_config.charset}"
        
        # 创建 MySQL 数据库连接
        db_kwargs = {"db_url": db_url}
        if agent_db_config.db_schema:
            db_kwargs["db_schema"] = agent_db_config.db_schema
        
        db = MySQLDb(**db_kwargs)
        logger.info(f"✓ MySQL 数据库连接成功: {mysql_config.host}:{mysql_config.port}/{mysql_config.database}")
        
        # ========== Milvus 配置 ==========
        milvus_config = config.milvus
        embedding_config = config.embedding
        
        # 构建 Milvus URI（远程服务器格式：http://host:port）
        milvus_uri = f"http://{milvus_config.host}:{milvus_config.port}"
        
        # 设置 OpenAI 兼容 API 的环境变量（如果配置了自定义 api_base）
        # OpenAIEmbedder 会从环境变量中读取 OPENAI_API_BASE 和 OPENAI_API_KEY
        if embedding_config.api_base:
            os.environ["OPENAI_API_BASE"] = embedding_config.api_base
        if embedding_config.api_key:
            os.environ["OPENAI_API_KEY"] = embedding_config.api_key
        
        # 创建嵌入模型
        # OpenAIEmbedder 只接受 id 参数，api_key 和 api_base 通过环境变量传递
        embedder = OpenAIEmbedder(
            id=embedding_config.model_name,
        )
        
        # 创建 Milvus 向量数据库实例
        vector_db = Milvus(
            collection=milvus_config.collection_name,
            uri=milvus_uri,
            search_type=SearchType.hybrid,  # 使用混合搜索（向量 + 关键词）
            embedder=embedder,
        )
        
        # 创建知识库实例
        knowledge = Knowledge(
            vector_db=vector_db,
        )
        
        logger.info(f"✓ Milvus 向量数据库连接成功: {milvus_uri}")
        logger.info(f"  Collection: {milvus_config.collection_name}, Dimension: {milvus_config.dimension}")
        logger.info(f"  Embedding Model: {embedding_config.model_name}")
        
        # ========== 创建 Agent ==========
        assistant = Agent(
            name="Assistant",
            model=model,  # 使用配置文件中定义的模型
            db=db,  # 使用 MySQL 数据库进行会话持久化
            knowledge=knowledge,  # 使用 Milvus 作为知识库
            search_knowledge=True,  # 启用知识库搜索
            add_knowledge_to_context=True,  # 将知识库内容添加到上下文
            instructions=[
                "你是一个有用的 AI 助手，可以访问知识库。",
                "回答问题时，请使用知识库检索相关信息。",
                "在提供答案时，请引用知识库中的来源。",
            ],
            markdown=True,
            add_history_to_context=True,  # 启用历史记录上下文
            num_history_runs=agent_db_config.num_history_runs,  # 历史记录数量
        )
        
        # ========== 创建 AgentOS ==========
        _agent_os = AgentOS(
            id="my-first-os",
            description="My first AgentOS with MySQL and Milvus support",
            agents=[assistant],
        )
        
        logger.info("✓ AgentOS 初始化成功")
        return _agent_os
        
    except Exception as e:
        logger.error(f"AgentOS 初始化失败: {e}", exc_info=True)
        raise


def get_agent_os_app():
    """
    获取 AgentOS 的 FastAPI 应用实例。
    
    Returns:
        FastAPI 应用实例
    """
    global _agent_os_app
    
    if _agent_os_app is not None:
        return _agent_os_app
    
    if _agent_os is None:
        create_agent_os()
    
    # 检查 _agent_os 是否成功创建
    if _agent_os is None:
        raise RuntimeError("AgentOS 初始化失败，无法创建 FastAPI 应用")
    
    _agent_os_app = _agent_os.get_app()
    return _agent_os_app

