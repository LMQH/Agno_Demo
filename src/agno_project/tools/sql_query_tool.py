"""SQL 查询工具。"""
from typing import Optional, Dict, Any, List
from agno.tools import Function
from ..config import get_config
from ..database.mysql_client import MySQLClient
import logging

logger = logging.getLogger(__name__)


class SQLQueryTool(Function):
    """SQL 查询工具，用于执行数据库查询。
    
    支持执行 SELECT、INSERT、UPDATE、DELETE 等 SQL 语句。
    会自动格式化查询结果，便于 Agent 理解。
    """
    
    def __init__(self, mysql_client: Optional[MySQLClient] = None):
        """初始化 SQL 查询工具。
        
        Args:
            mysql_client: MySQL 客户端实例，如果为 None 则自动创建
        """
        super().__init__(
            name="sql_query",
            description="执行 SQL 查询以获取数据库中的数据。支持 SELECT、INSERT、UPDATE、DELETE 等 SQL 语句。",
            args={
                "query": {
                    "type": "string",
                    "description": "要执行的 SQL 查询语句",
                    "required": True
                }
            }
        )
        self.config = get_config()
        self.mysql_client = mysql_client or MySQLClient()
    
    def _is_safe_query(self, query: str) -> bool:
        """检查 SQL 查询是否安全（基本安全检查）。
        
        Args:
            query: SQL 查询语句
        
        Returns:
            是否安全
        """
        query_upper = query.upper().strip()
        
        # 禁止的危险操作（防止数据库结构被破坏）
        dangerous_operations = [
            "DROP DATABASE",
            "DROP TABLE",
            "TRUNCATE",
            "ALTER TABLE",
            "CREATE TABLE",
            "CREATE DATABASE",
            # 注意：允许 DELETE、UPDATE、INSERT 操作，但需要谨慎使用
        ]
        
        for op in dangerous_operations:
            if op in query_upper:
                logger.warning(f"检测到危险操作: {op}")
                return False
        
        return True
    
    def _format_results(self, rows: List[Any], query_type: str) -> str:
        """格式化查询结果。
        
        Args:
            rows: 查询结果行
            query_type: 查询类型（SELECT, INSERT, UPDATE, DELETE）
        
        Returns:
            格式化后的结果字符串
        """
        # SELECT 查询：格式化表格数据
        if query_type == "SELECT":
            if not rows or len(rows) == 0:
                return "查询结果为空，没有找到匹配的数据。"
            
            # 将 Row 对象转换为字典（如果可能）
            formatted_rows = []
            for row in rows:
                if hasattr(row, '_asdict'):
                    # SQLAlchemy Row 对象
                    formatted_rows.append(row._asdict())
                elif hasattr(row, '_mapping'):
                    # SQLAlchemy Row 对象（新版本）
                    formatted_rows.append(dict(row._mapping))
                elif isinstance(row, (list, tuple)):
                    # 元组或列表
                    formatted_rows.append(row)
                else:
                    formatted_rows.append(str(row))
            
            # 格式化输出
            result_lines = [f"查询返回 {len(formatted_rows)} 行结果：\n"]
            
            for i, row in enumerate(formatted_rows, 1):
                if isinstance(row, dict):
                    row_str = "\n".join([f"  {key}: {value}" for key, value in row.items()])
                    result_lines.append(f"[行 {i}]\n{row_str}")
                else:
                    result_lines.append(f"[行 {i}]\n  {row}")
                result_lines.append("")  # 空行分隔
            
            return "\n".join(result_lines)
        
        # 其他操作（INSERT, UPDATE, DELETE）：返回影响的行数
        else:
            # 对于非 SELECT 操作，rows 通常是空列表，实际影响的行数需要从结果中获取
            # 这里简化处理，如果有行数据就显示行数
            if isinstance(rows, list):
                if len(rows) > 0:
                    return f"{query_type} 操作执行成功，返回了 {len(rows)} 行数据。"
                else:
                    return f"{query_type} 操作执行成功。"
            else:
                return f"{query_type} 操作执行成功。"
    
    async def run(self, query: str) -> str:
        """执行 SQL 查询。
        
        Args:
            query: SQL 查询语句
        
        Returns:
            查询结果（格式化后的字符串）
        """
        try:
            logger.debug(f"执行 SQL 查询: {query[:100]}...")
            
            # 基本安全检查
            if not self._is_safe_query(query):
                error_msg = "查询包含危险操作，已被拒绝执行。只允许 SELECT、INSERT、UPDATE、DELETE 操作。"
                logger.warning(error_msg)
                return error_msg
            
            # 判断查询类型
            query_upper = query.strip().upper()
            if query_upper.startswith("SELECT"):
                query_type = "SELECT"
            elif query_upper.startswith("INSERT"):
                query_type = "INSERT"
            elif query_upper.startswith("UPDATE"):
                query_type = "UPDATE"
            elif query_upper.startswith("DELETE"):
                query_type = "DELETE"
            else:
                query_type = "UNKNOWN"
            
            # 执行查询
            # 注意：execute_query 是同步方法，需要在异步环境中调用
            import asyncio
            rows = await asyncio.to_thread(self.mysql_client.execute_query, query)
            
            # 格式化结果
            result = self._format_results(rows, query_type)
            row_count = len(rows) if isinstance(rows, list) else (1 if rows else 0)
            logger.debug(f"SQL 查询执行成功（类型: {query_type}），返回 {row_count} 行结果")
            return result
            
        except Exception as e:
            error_msg = f"SQL 查询执行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

