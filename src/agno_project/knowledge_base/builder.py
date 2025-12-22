"""用于处理和存储文档的知识库构建器。"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import shutil
import time
import asyncio
import logging
from datetime import datetime

from .chunkers import ChunkerFactory, BaseChunker
from .embedder import EmbeddingGenerator
from ..database.mysql_client import MySQLClient
from ..database.milvus_client import MilvusClient
from ..config import get_config

# 配置日志
logger = logging.getLogger(__name__)


class KnowledgeBaseBuilder:
    """从文档构建和管理知识库。"""
    
    def __init__(
        self,
        mysql_client: Optional[MySQLClient] = None,
        milvus_client: Optional[MilvusClient] = None,
        embedder: Optional[EmbeddingGenerator] = None
    ):
        """初始化知识库构建器。"""
        self.mysql_client = mysql_client or MySQLClient()
        self.milvus_client = milvus_client or MilvusClient()
        self.embedder = embedder or EmbeddingGenerator()
        self.config = get_config()
        
        # 初始化数据库表
        self.mysql_client.create_tables()
        
        # 初始化知识库文件存储目录
        project_root = Path(__file__).parent.parent.parent.parent
        self.knowledge_base_dir = project_root / "data" / "knowledge_base"
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
    
    async def _read_markdown_file(self, file_path: Path) -> str:
        """异步读取 Markdown 文件内容。"""
        try:
            # 使用异步文件读取，避免阻塞事件循环
            def _read_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, _read_file)
            return content
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
    
    def _read_markdown_file_sync(self, file_path: Path) -> str:
        """同步读取 Markdown 文件内容（用于需要同步的场景）。"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")
    
    async def add_document(
        self,
        file_path: str,
        chunk_method: str = "markdown",
        metadata: Optional[Dict] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """向知识库添加文档。
        
        Args:
            file_path: 文件路径
            chunk_method: 切分方法
            metadata: 元数据
            content: 文件内容（如果提供，则跳过文件读取）
        """
        source_file = Path(file_path)
        
        # 记录开始时间
        start_time = time.time()
        
        # 读取文件内容（如果未提供）
        content_to_save = None  # 保存用于文件写入的内容
        if content is None:
            if not source_file.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            logger.debug(f"开始处理文件: {source_file}")
            content = await self._read_markdown_file(source_file)
            content_to_save = content  # 保存内容用于后续文件写入
        else:
            logger.debug(f"使用提供的文件内容，文件路径: {source_file}")
            content_to_save = content  # 保存内容用于后续文件写入
        
        logger.debug(f"文件内容读取完成，大小: {len(content)} 字符")
        
        # 创建切分器
        logger.debug("开始创建切分器")
        chunker = ChunkerFactory.create_chunker(
            method=chunk_method,
            chunk_size=self.config.rag.chunk_size,
            chunk_overlap=self.config.rag.chunk_overlap
        )
        logger.debug(f"切分器创建完成: method={chunk_method}, chunk_size={self.config.rag.chunk_size}")
        
        # 切分文档（在后台线程执行，避免阻塞）
        logger.debug("开始切分文档")
        chunk_start_time = time.time()
        try:
            loop = asyncio.get_event_loop()
            # 使用ProcessPoolExecutor对于CPU密集型任务可能更好，但ThreadPoolExecutor对I/O更友好
            # 这里保持使用默认的ThreadPoolExecutor，因为chunk操作主要是字符串操作
            chunks = await loop.run_in_executor(None, chunker.chunk, content, metadata)
            chunk_time = time.time() - chunk_start_time
            logger.debug(f"文档切分完成: {len(chunks)} 个chunks，耗时 {chunk_time:.2f}秒")
        except Exception as e:
            logger.error(f"文档切分失败: {str(e)}", exc_info=True)
            raise
        finally:
            # 立即释放content内存，即使在异常情况下也要释放
            # 但保留content_to_save用于文件写入
            del content
        
        if not chunks:
            raise ValueError("No chunks generated from document")
        
        # 使用原始文件名（去掉upload_前缀如果存在）
        file_extension = source_file.suffix if source_file.suffix else ".md"
        original_name = source_file.name
        # 如果原始文件名包含upload_前缀（来自API上传），去掉它
        if original_name.startswith("upload_"):
            original_name = original_name[7:]  # 去掉"upload_"前缀
        
        unique_file_name = original_name
        target_file_path = self.knowledge_base_dir / unique_file_name
        
        # 检查是否存在同名文件，如果存在则删除旧文件的所有记录
        existing_file_id = None
        with self.mysql_client.get_session() as session:
            from sqlalchemy import text
            result = session.execute(
                text("SELECT id FROM knowledge_files WHERE file_name = :file_name"),
                {"file_name": unique_file_name}
            ).fetchone()
            if result:
                existing_file_id = result[0]
                logger.debug(f"发现同名文件，将删除旧文件记录: file_id={existing_file_id}, file_name={unique_file_name}")
                # 删除旧文件的所有记录
                try:
                    # 从 Milvus 删除向量
                    self.milvus_client.delete_by_file_ids([existing_file_id])
                    logger.debug(f"已删除Milvus中的向量: file_id={existing_file_id}")
                    
                    # 从 MySQL 删除文件记录
                    session.execute(
                        text("DELETE FROM knowledge_files WHERE id = :file_id"),
                        {"file_id": existing_file_id}
                    )
                    session.commit()
                    logger.debug(f"已删除MySQL记录: file_id={existing_file_id}")
                    
                    # 删除文件
                    if target_file_path.exists():
                        target_file_path.unlink()
                        logger.debug(f"已删除文件: {target_file_path}")
                except Exception as e:
                    logger.warning(f"删除旧文件记录时出错（继续处理新文件）: {e}", exc_info=True)
                    session.rollback()
        
        # 异步保存文件到知识库目录
        if source_file.exists():
            # 如果源文件存在，复制文件
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, shutil.copy2, source_file, target_file_path)
            logger.debug(f"文件已保存: {target_file_path}")
        elif content_to_save is not None:
            # 如果源文件不存在但提供了内容，保存内容到文件
            def _write_file():
                target_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file_path, 'w', encoding='utf-8') as f:
                    f.write(content_to_save)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _write_file)
            logger.debug(f"文件已保存: {target_file_path}")
        else:
            logger.debug("跳过文件保存（无内容可保存）")
        
        # 释放content_to_save内存
        if content_to_save is not None:
            del content_to_save
        
        # 保存文件元数据到 MySQL
        logger.debug("开始写入MySQL")
        try:
            with self.mysql_client.get_session() as session:
                from sqlalchemy import text
                result = session.execute(
                    text("""
                        INSERT INTO knowledge_files (file_name, updated_at)
                        VALUES (:file_name, :updated_at)
                    """),
                    {
                        "file_name": unique_file_name,
                        "updated_at": datetime.utcnow()
                    }
                )
                session.commit()
                file_id = result.lastrowid
                logger.debug(f"MySQL记录已创建: file_id={file_id}, file_name={unique_file_name}")
        except Exception as e:
            logger.error(f"MySQL写入失败: {e}", exc_info=True)
            # 删除已保存的文件
            if target_file_path.exists():
                target_file_path.unlink()
            raise RuntimeError(f"数据库写入失败: {e}")
        
        # 优化：不预先提取所有chunk内容，而是按需处理
        # 这样可以避免chunk_contents占用大量内存
        num_chunks = len(chunks)
        logger.debug(f"准备处理 {num_chunks} 个chunks")
        
        # 注意：保留chunks引用，因为我们需要在循环中访问chunk["content"]
        # 但会在处理完每个批次后逐步释放
        
        # 优化批量大小计算：只计算前几个chunks的平均大小来估算
        sample_size = min(10, num_chunks)
        if sample_size > 0:
            sample_chars = sum(len(chunks[i]["content"]) for i in range(sample_size))
            avg_chunk_size = sample_chars / sample_size
        else:
            avg_chunk_size = 500  # 默认值
        logger.debug(f"估算平均chunk大小: {avg_chunk_size:.0f} 字符（基于前 {sample_size} 个chunks）")
        
        # 动态调整批量大小（减小批量大小，降低内存占用）
        if avg_chunk_size > 1000:
            batch_size = 10  # 减小批量大小
        elif avg_chunk_size > 500:
            batch_size = 20
        else:
            batch_size = 30  # 减小批量大小
        
        total_batches = (num_chunks + batch_size - 1) // batch_size
        
        logger.debug(f"开始生成嵌入向量: {num_chunks} 个chunks，平均大小 {avg_chunk_size:.0f} 字符，分 {total_batches} 批处理（每批 {batch_size} 个）")
        embedding_start_time = time.time()
        insert_start_time = time.time()
        
        # 修复：立即插入，不累积，避免内存泄漏
        # 每批生成后立即插入，然后释放内存
        insert_batch_size = 3  # 每3批flush一次，减少flush频率
        inserted_count = 0
        
        try:
            for i in range(0, num_chunks, batch_size):
                # 按需提取当前批次的content，不预先提取所有
                batch = [chunks[j]["content"] for j in range(i, min(i + batch_size, num_chunks))]
                batch_num = i // batch_size + 1
                
                # 生成当前批次的嵌入向量（添加超时和日志）
                logger.debug(f"批次 {batch_num}/{total_batches}: 开始生成嵌入向量（{len(batch)} 个chunks）")
                try:
                    batch_embeddings = await asyncio.wait_for(
                        self.embedder.generate_embeddings(batch),
                        timeout=300.0  # 5分钟超时
                    )
                    logger.debug(f"批次 {batch_num}: 嵌入向量生成完成，共 {len(batch_embeddings)} 个向量")
                except asyncio.TimeoutError:
                    logger.error(f"批次 {batch_num}: 嵌入向量生成超时（超过5分钟）")
                    raise RuntimeError(f"嵌入向量生成超时（批次 {batch_num}）")
                except Exception as e:
                    logger.error(f"批次 {batch_num}: 嵌入向量生成失败: {e}", exc_info=True)
                    raise RuntimeError(f"嵌入向量生成失败（批次 {batch_num}）: {e}")
                
                # 立即插入，不累积
                try:
                    insert_result = self.milvus_client.insert_vectors(
                        file_ids=[file_id] * len(batch),
                        file_names=[unique_file_name] * len(batch),
                        contents=batch,
                        embeddings=batch_embeddings,
                        flush=False
                    )
                    inserted_count += len(batch)
                    logger.debug(f"批次 {batch_num}: 成功插入 {len(batch)} 个向量到Milvus")
                    
                    # 立即释放内存（非常重要！）
                    del batch_embeddings
                    del batch
                    del insert_result
                    # 强制垃圾回收（对于大对象）
                    if batch_num % 10 == 0:
                        import gc
                        gc.collect()
                        logger.debug(f"批次 {batch_num}: 执行垃圾回收")
                    
                    # 每几批flush一次
                    if batch_num % insert_batch_size == 0:
                        self.milvus_client.collection.flush()
                        logger.debug(f"已插入 {inserted_count} 个向量到Milvus并flush")
                except Exception as e:
                    logger.error(f"插入向量失败（批次 {batch_num}）: {e}", exc_info=True)
                    # 立即释放内存，即使失败也要释放
                    try:
                        del batch_embeddings
                        del batch
                    except:
                        pass
                    # 如果插入失败，回滚MySQL记录
                    try:
                        with self.mysql_client.get_session() as session:
                            from sqlalchemy import text
                            session.execute(
                                text("DELETE FROM knowledge_files WHERE id = :file_id"),
                                {"file_id": file_id}
                            )
                            session.commit()
                            logger.debug(f"已回滚MySQL记录: file_id={file_id}")
                    except Exception as rollback_error:
                        logger.error(f"回滚MySQL记录失败: {rollback_error}")
                    raise RuntimeError(f"向量插入失败（批次 {batch_num}）: {e}")
                
                # 减少延迟时间
                if batch_num < total_batches:
                    if batch_num % 5 == 0:
                        await asyncio.sleep(0.1)
                    else:
                        await asyncio.sleep(0.02)
            
            embedding_time = time.time() - embedding_start_time
            logger.info(f"嵌入向量生成完成，耗时 {embedding_time:.2f}秒")
            
            # 最后flush一次，确保所有数据写入
            self.milvus_client.collection.flush()
            insert_time = time.time() - insert_start_time
            logger.info(f"向量插入完成，共插入 {inserted_count} 个向量，耗时 {insert_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"处理嵌入向量时发生错误: {e}", exc_info=True)
            # 清理：删除已插入的向量
            try:
                self.milvus_client.delete_by_file_ids([file_id])
                logger.debug(f"已清理Milvus中的向量: file_id={file_id}")
            except Exception as cleanup_error:
                logger.error(f"清理Milvus向量失败: {cleanup_error}")
            # 删除MySQL记录
            try:
                with self.mysql_client.get_session() as session:
                    from sqlalchemy import text
                    session.execute(
                        text("DELETE FROM knowledge_files WHERE id = :file_id"),
                        {"file_id": file_id}
                    )
                    session.commit()
                    logger.debug(f"已清理MySQL记录: file_id={file_id}")
            except Exception as cleanup_error:
                logger.error(f"清理MySQL记录失败: {cleanup_error}")
            # 删除文件
            try:
                if target_file_path.exists():
                    target_file_path.unlink()
                    logger.debug(f"已删除文件: {target_file_path}")
            except Exception as cleanup_error:
                logger.error(f"删除文件失败: {cleanup_error}")
            raise
        
        # 最后释放chunks引用
        del chunks
        
        total_time = time.time() - start_time
        logger.info(f"文件处理完成: {unique_file_name}，总耗时 {total_time:.2f}秒")
        
        return {
            "file_id": file_id,
            "status": "success",
            "chunks_count": inserted_count,  # 使用实际插入的数量
            "file_name": unique_file_name,
            "processing_time": round(total_time, 2)
        }
    
    def delete_document(self, file_id: int) -> Dict[str, Any]:
        """从知识库中删除文档及其向量。"""
        # 获取文件信息
        with self.mysql_client.get_session() as session:
            from sqlalchemy import text
            result = session.execute(
                text("SELECT file_name FROM knowledge_files WHERE id = :file_id"),
                {"file_id": file_id}
            ).fetchone()
            
            if not result:
                raise ValueError(f"File with id {file_id} not found")
            
            file_name = result[0]
        
        # 从 Milvus 删除向量
        self.milvus_client.delete_by_file_ids([file_id])
        
        # 从 MySQL 删除文件记录
        with self.mysql_client.get_session() as session:
            from sqlalchemy import text
            session.execute(
                text("DELETE FROM knowledge_files WHERE id = :file_id"),
                {"file_id": file_id}
            )
            session.commit()
        
        # 删除文件（可选：根据需求决定是否删除磁盘文件）
        file_path = self.knowledge_base_dir / file_name
        if file_path.exists():
            file_path.unlink()
        
        return {
            "file_id": file_id,
            "status": "deleted",
            "file_name": file_name
        }
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """列出知识库中的所有文档。"""
        with self.mysql_client.get_session() as session:
            from sqlalchemy import text
            results = session.execute(
                text("""
                    SELECT id, file_name, updated_at
                    FROM knowledge_files
                    ORDER BY updated_at DESC
                """)
            ).fetchall()
            
            documents = []
            for row in results:
                file_id, file_name, updated_at = row
                documents.append({
                    "id": file_id,
                    "file_name": file_name,
                    "updated_at": updated_at.isoformat() if updated_at else None
                })
            
            return documents

