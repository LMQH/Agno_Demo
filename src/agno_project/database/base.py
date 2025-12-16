"""基础数据库工具和接口。"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStoreInterface(ABC):
    """向量存储操作接口。"""
    
    @abstractmethod
    def insert_vectors(
        self,
        chunk_ids: List[int],
        document_ids: List[int],
        contents: List[str],
        embeddings: List[List[float]]
    ) -> List[int]:
        """将向量插入向量存储。"""
        pass
    
    @abstractmethod
    def search_vectors(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        expr: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """搜索相似向量。"""
        pass
    
    @abstractmethod
    def delete_by_chunk_ids(self, chunk_ids: List[int]):
        """根据切片 ID 删除向量。"""
        pass


class DocumentStoreInterface(ABC):
    """文档存储操作接口。"""
    
    @abstractmethod
    def save_document(self, file_name: str, file_path: str, metadata: Optional[Dict] = None) -> int:
        """保存文档元数据。"""
        pass
    
    @abstractmethod
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取文档。"""
        pass
    
    @abstractmethod
    def save_chunks(self, document_id: int, chunks: List[Dict[str, Any]]) -> List[int]:
        """保存文档切片。"""
        pass
    
    @abstractmethod
    def get_chunks_by_document(self, document_id: int) -> List[Dict[str, Any]]:
        """获取文档的所有切片。"""
        pass

