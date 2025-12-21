"""数据库基础接口定义。"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseDatabase(ABC):
    """数据库基础接口。"""
    
    @abstractmethod
    async def connect(self) -> None:
        """建立数据库连接。"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """关闭数据库连接。"""
        pass

