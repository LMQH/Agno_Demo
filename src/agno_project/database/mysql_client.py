"""MySQL 数据库客户端。"""
from typing import Optional
from sqlalchemy import create_engine, text  # type: ignore
from sqlalchemy.orm import sessionmaker, Session  # type: ignore
from sqlalchemy.pool import QueuePool  # type: ignore
from contextlib import contextmanager
import pymysql

from ..config import get_config, MySQLConfig


class MySQLClient:
    """带连接池的 MySQL 数据库客户端。"""
    
    def __init__(self, config: Optional[MySQLConfig] = None):
        """初始化 MySQL 客户端。"""
        if config is None:
            config = get_config().mysql
        
        self.config = config
        self._ensure_database_exists()
        
        self.engine = create_engine(
            f"mysql+pymysql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}?charset={config.charset}",
            poolclass=QueuePool,
            pool_size=config.pool_size,
            pool_pre_ping=True,
            echo=False
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
    
    def _ensure_database_exists(self):
        """确保数据库存在，如果不存在则创建。"""
        try:
            # 先连接到 MySQL 服务器（不指定数据库）
            connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                charset=self.config.charset
            )
            
            with connection.cursor() as cursor:
                # 检查数据库是否存在
                cursor.execute(f"SHOW DATABASES LIKE '{self.config.database}'")
                result = cursor.fetchone()
                
                if not result:
                    # 数据库不存在，创建它
                    cursor.execute(f"CREATE DATABASE `{self.config.database}` CHARACTER SET {self.config.charset} COLLATE {self.config.charset}_unicode_ci")
                    connection.commit()
                    print(f"数据库 '{self.config.database}' 已创建")
                else:
                    print(f"数据库 '{self.config.database}' 已存在")
            
            connection.close()
        except Exception as e:
            print(f"警告: 无法自动创建数据库 '{self.config.database}': {e}")
            print(f"请手动创建数据库: CREATE DATABASE `{self.config.database}` CHARACTER SET {self.config.charset} COLLATE {self.config.charset}_unicode_ci;")
            raise
    
    @contextmanager
    def get_session(self):
        """获取数据库会话上下文管理器。"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[dict] = None):
        """执行原始 SQL 查询。"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result.fetchall()
    
    def create_tables(self):
        """为 RAG 系统创建必要的表。"""
        from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, Index  # type: ignore
        from datetime import datetime
        
        metadata = MetaData()
        
        # 知识文件列表表：只存储文件元数据，不存储文件内容
        knowledge_files_table = Table(
            'knowledge_files',
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True, comment='文件ID，主键，自增'),
            Column('file_name', String(255), nullable=False, comment='文件名'),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最新更新时间'),
            Index('idx_file_name', 'file_name')
        )
        
        metadata.create_all(self.engine)
        
        # 为表添加中文注释和迁移现有表结构
        with self.get_session() as session:
            # 检查并删除content_hash列（如果存在）
            try:
                session.execute(text("SELECT content_hash FROM knowledge_files LIMIT 1"))
                # 列存在，删除它
                try:
                    # 先删除索引
                    session.execute(text("DROP INDEX idx_content_hash ON knowledge_files"))
                except Exception:
                    pass  # 索引可能不存在，忽略错误
                # 删除列
                session.execute(text("ALTER TABLE knowledge_files DROP COLUMN content_hash"))
                session.commit()
                print("已删除content_hash列和索引")
            except Exception:
                # 列不存在，无需处理
                session.rollback()
                pass
            
            # 为knowledge_files表添加注释
            try:
                session.execute(text("ALTER TABLE knowledge_files COMMENT = '知识文件列表表，存储知识库文件的元数据信息（文件ID、文件名、更新时间）'"))
                session.commit()
            except Exception:
                session.rollback()
        
        return True

