"""不同环境的配置管理。"""
import os
import platform
import socket
import logging
from pathlib import Path
from typing import Literal, Optional, List
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# 生产服务器列表(内网以172.16.64开头)
PROD_LIST = [
    "172.16.64.100",    # 100生产
    "172.16.64.101",   # 101生产
    "172.16.64.103",   # 103生产
]

# 预演服务器列表
PREVIEW_LIST = [
    "172.16.64.105",    # 105预演
    "172.16.64.104",    # 104预演
]


class MySQLConfig(BaseSettings):
    """MySQL 数据库配置。"""
    host: str
    port: int = 3306
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"
    pool_size: int = 5


class MilvusConfig(BaseSettings):
    """Milvus 向量数据库配置。"""
    host: str
    port: int = 19530
    database: str = "default"  # Milvus 数据库名称，默认为 "default"
    collection_name: str
    dimension: int = 1024  # 向量维度，默认为 1024
    index_type: str = "IVF_FLAT"  # 索引类型，默认为 "IVF_FLAT"
    metric_type: str = "COSINE"  # 距离度量类型，默认为 "COSINE"


class EmbeddingConfig(BaseSettings):
    """嵌入模型配置。"""
    provider: str = "openai"
    model_name: str = "text-embedding-v4"
    api_key: str = ""
    api_base: str = ""
    dimension: int = 1024


class LLMConfig(BaseSettings):
    """LLM 模型配置。"""
    provider: str = "custom"
    model_name: str = "deepseek-v3.2-exp"
    api_base: str = ""
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000


class RAGConfig(BaseSettings):
    """RAG 系统配置。"""
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    similarity_threshold: float = 0.7


class AgentDbConfig(BaseSettings):
    """Agno Agent 数据库配置（用于会话持久性）。
    
    现在使用 MySQLDb 连接 MySQL，不再需要 db_type、db_file 和 db_id。
    这些字段保留仅用于向后兼容，实际不再使用。
    """
    enabled: bool = True
    db_type: Optional[str] = None  # 已废弃，不再使用
    db_file: Optional[str] = None  # 已废弃，不再使用
    db_id: Optional[str] = None  # 已废弃，不再使用
    num_history_runs: int = 5  # 历史记录运行次数，用于控制添加到上下文的历史消息数量
    db_schema: Optional[str] = None  # 数据库 schema 名称，用于生成表名（如 "agno_demo"），默认为 "ai"
    session_table: Optional[str] = None  # 自定义会话表名，如果为 None 则使用 {db_schema}_sessions
    memory_table: Optional[str] = None  # 自定义记忆表名，如果为 None 则使用 {db_schema}_memories


# AgentOSConfig 已移除，简化实现，参考官方示例


def get_local_ip() -> str:
    """
    跨平台获取本地 IP 地址：
    - Linux: 优先尝试 eth0（云服务器内网 IP），失败则回退到 socket.connect
    - Windows/macOS: 使用 socket.connect 获取默认出口 IP
    """
    system = platform.system().lower()
    
    if system == "linux":
        # 尝试直接读取 eth0（适用于云服务器）
        try:
            import fcntl
            import struct
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR，用于"获取接口地址"
                struct.pack('256s', b'eth0')
            )[20:24])
            logger.debug(f"[Linux] 通过 eth0 获取内网 IP: {ip}")
            return ip
        except Exception as e:
            logger.debug(f"读取 eth0 失败，回退到通用方法: {e}")
    
    # 通用方法：适用于 Windows / macOS / Linux 回退
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到公网地址（不会发送数据）
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        logger.debug(f"[{system}] 通过 socket.connect 获取 IP: {ip}")
        return ip
    except Exception as e:
        logger.error(f"获取本地 IP 失败: {e}")
        return "127.0.0.1"


def detect_environment() -> Literal["dev", "show", "prod"]:
    """
    根据IP地址自动检测环境。
    如果IP在生产服务器列表中，返回 "prod"
    如果IP在预演服务器列表中，返回 "show"
    否则返回 "dev"
    """
    # 优先使用环境变量
    env = os.getenv("ENVIRONMENT")
    if env in ["dev", "show", "prod"]:
        logger.info(f"使用环境变量指定的环境: {env}")
        return env
    
    # 根据IP自动检测
    ip = get_local_ip()
    
    if ip in PROD_LIST:
        logger.info(f"当前IP地址 {ip} 在生产服务器列表中，使用生产环境配置")
        return "prod"
    elif ip in PREVIEW_LIST:
        logger.info(f"当前IP地址 {ip} 在预演服务器列表中，使用预演环境配置")
        return "show"
    else:
        logger.info(f"当前IP地址 {ip} 未在生产或预演服务器列表中，使用开发环境配置")
        return "dev"


class AppConfig(BaseSettings):
    """应用程序配置。"""
    name: str = "agno-rag-system"
    environment: Literal["dev", "show", "prod"] = "dev"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    mysql: MySQLConfig
    milvus: MilvusConfig
    embedding: EmbeddingConfig
    llm: LLMConfig
    rag: RAGConfig
    agent_db: AgentDbConfig
    # agentos 配置已移除，简化实现

    @classmethod
    def load_from_toml(cls, env: Literal["dev", "show", "prod"] = None) -> "AppConfig":
        """根据环境从 TOML 文件加载配置。"""
        if env is None:
            env = detect_environment()
        
        config_path = Path(__file__).parent.parent.parent / "config" / f"{env}.toml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        logger.debug(f"加载配置文件: {config_path}")
        
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
        
        # 构建嵌套配置对象
        app_config = config_data.get("app", {})
        db_config = config_data.get("database", {})
        model_config = config_data.get("model", {})
        rag_config = config_data.get("rag", {})
        agent_db_config = config_data.get("agent_db", {})
        # agentos 配置已移除，简化实现
        
        return cls(
            **app_config,
            mysql=MySQLConfig(**db_config.get("mysql", {})),
            milvus=MilvusConfig(**db_config.get("milvus", {})),
            embedding=EmbeddingConfig(**model_config.get("embedding", {})),
            llm=LLMConfig(**model_config.get("llm", {})),
            rag=RAGConfig(**rag_config),
            agent_db=AgentDbConfig(**agent_db_config),
            # agentos 已移除
        )


# 全局配置实例
_config: AppConfig = None


def get_config() -> AppConfig:
    """获取全局配置实例。"""
    global _config
    if _config is None:
        _config = AppConfig.load_from_toml()
    return _config

