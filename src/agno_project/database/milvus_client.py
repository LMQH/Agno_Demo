"""Milvus vector database client."""
from typing import List, Optional, Dict, Any
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
    MilvusException
)

from ..config import get_config, MilvusConfig


class MilvusClient:
    """Milvus 向量数据库客户端。"""
    
    def __init__(self, config: Optional[MilvusConfig] = None):
        """初始化 Milvus 客户端。"""
        if config is None:
            config = get_config().milvus
        
        self.config = config
        self.connection_name = f"default_{config.collection_name}"
        self._connect()
        self._ensure_collection()
    
    def _connect(self):
        """连接到 Milvus 服务器。"""
        try:
            # 构建连接参数
            connect_params = {
                "alias": self.connection_name,
                "host": self.config.host,
                "port": self.config.port
            }
            # 如果指定了数据库，则添加 db_name 参数
            if hasattr(self.config, 'database') and self.config.database:
                connect_params["db_name"] = self.config.database
            
            connections.connect(**connect_params)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Milvus: {e}")
    
    def _ensure_collection(self):
        """确保集合存在，如果不存在则创建。"""
        if utility.has_collection(self.config.collection_name, using=self.connection_name):
            self.collection = Collection(
                self.config.collection_name,
                using=self.connection_name
            )
        else:
            self._create_collection()
    
    def _create_collection(self):
        """使用模式创建集合。"""
        # 定义模式
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True, description="向量ID，主键，自增"),
            FieldSchema(name="file_id", dtype=DataType.INT64, description="文件ID，关联knowledge_files表"),
            FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=255, description="文件名"),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535, description="文档切片内容文本"),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.config.dimension, description="向量嵌入，维度为{}".format(self.config.dimension)),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="RAG系统向量集合，用于存储文档切片的向量嵌入和元数据，支持相似度搜索"
        )
        
        # 创建集合
        self.collection = Collection(
            name=self.config.collection_name,
            schema=schema,
            using=self.connection_name
        )
        
        # 创建索引
        index_params = {
            "metric_type": self.config.metric_type,
            "index_type": self.config.index_type,
            "params": {"nlist": 32}
        }
        
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
    
    def insert_vectors(
        self,
        file_ids: List[int],
        file_names: List[str],
        contents: List[str],
        embeddings: List[List[float]],
        flush: bool = True
    ) -> List[int]:
        """将向量插入集合。
        
        Args:
            file_ids: 文件ID列表
            file_names: 文件名列表
            contents: 内容列表
            embeddings: 嵌入向量列表
            flush: 是否立即flush到磁盘，默认True。批量插入时建议设为False，最后统一flush
        """
        if not all(len(lst) == len(file_ids) for lst in [file_names, contents, embeddings]):
            raise ValueError("All input lists must have the same length")
        
        data = [
            file_ids,
            file_names,
            contents,
            embeddings
        ]
        
        try:
            insert_result = self.collection.insert(data)
            primary_keys = insert_result.primary_keys
            
            # 立即释放data和insert_result的内存
            del data
            del insert_result
            
            if flush:
                self.collection.flush()
            
            return primary_keys
        except Exception as e:
            # 即使失败也要释放内存
            try:
                del data
            except:
                pass
            raise RuntimeError(f"Failed to insert vectors: {e}")
    
    def search_vectors(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[List[Dict[str, Any]]]:
        """搜索相似向量。"""
        if output_fields is None:
            output_fields = ["file_id", "file_name", "content"]
        
        search_params = {
            "metric_type": self.config.metric_type,
            "params": {"nprobe": 10}
        }
        
        try:
            results = self.collection.search(
                data=query_embeddings,
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=output_fields
            )
            
            # 格式化结果
            formatted_results = []
            for result in results:
                hits = []
                for hit in result:
                    # 对于 COSINE 距离，距离越小表示越相似，相似度 = 1 - distance
                    # 对于 L2 距离，距离越大表示越不相似，相似度 = 1 / (1 + distance) 或使用其他转换
                    if self.config.metric_type == "COSINE":
                        score = 1 - hit.distance
                    elif self.config.metric_type == "L2":
                        score = 1 / (1 + hit.distance)  # 将L2距离转换为相似度
                    else:
                        score = hit.distance
                    
                    hits.append({
                        "id": hit.id,
                        "distance": hit.distance,
                        "file_id": hit.entity.get("file_id"),
                        "file_name": hit.entity.get("file_name"),
                        "content": hit.entity.get("content"),
                        "score": score
                    })
                formatted_results.append(hits)
            
            return formatted_results
        except Exception as e:
            raise RuntimeError(f"Failed to search vectors: {e}")
    
    def delete_by_file_ids(self, file_ids: List[int]):
        """根据文件 ID 删除向量。"""
        if not file_ids:
            return
        # 构建表达式：file_id in [1, 2, 3]
        expr = f"file_id in [{','.join(map(str, file_ids))}]"
        try:
            self.collection.delete(expr)
            self.collection.flush()
        except Exception as e:
            raise RuntimeError(f"Failed to delete vectors: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息。"""
        try:
            stats = self.collection.num_entities
            return {
                "collection_name": self.config.collection_name,
                "num_entities": stats,
                "dimension": self.config.dimension
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get collection stats: {e}")
    
    def close(self):
        """关闭连接。"""
        try:
            connections.disconnect(self.connection_name)
        except Exception:
            pass

