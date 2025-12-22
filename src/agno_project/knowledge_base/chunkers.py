"""使用 Agno 框架的文档切分方法。"""
import re
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

# 尝试导入Agno的MarkdownChunking和Document
try:
    from agno.knowledge.chunking.markdown import MarkdownChunking  # type: ignore
    from agno.knowledge.document.base import Document  # type: ignore
    AGNO_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    AGNO_AVAILABLE = False
    logging.warning(f"Agno框架未安装，将无法使用MarkdownChunking。错误: {e}。请运行: pip install agno unstructured")
except Exception as e:
    # 捕获其他可能的异常（如依赖问题）
    AGNO_AVAILABLE = False
    logging.warning(f"Agno框架导入失败: {type(e).__name__}: {e}。请检查依赖是否完整安装。")

from .utils import extract_images_from_text, extract_structure_info

logger = logging.getLogger(__name__)


class BaseChunker(ABC):
    """基础切分器接口。"""
    
    @abstractmethod
    def chunk(self, content: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """将内容切分为更小的片段。"""
        pass


class RecursiveCharacterChunker(BaseChunker):
    """递归字符切分器（类似于 LangChain 的方法，作为fallback）。"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """初始化切分器。"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, content: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """递归切分内容。"""
        if not content:
            return []
        
        chunks = []
        start = 0
        content_length = len(content)
        
        while start < content_length:
            end = start + self.chunk_size
            
            # 尝试在句子边界处断开
            if end < content_length:
                # 查找句子结尾
                sentence_endings = ['. ', '。', '!\n', '?\n', '.\n']
                best_break = end
                
                for ending in sentence_endings:
                    pos = content.rfind(ending, start, end)
                    if pos != -1:
                        best_break = pos + len(ending)
                        break
                
                # 如果没有句子边界，尝试段落分隔
                if best_break == end:
                    para_break = content.rfind('\n\n', start, end)
                    if para_break != -1:
                        best_break = para_break + 2
                    else:
                        # 尝试单个换行符
                        newline_break = content.rfind('\n', start, end)
                        if newline_break != -1:
                            best_break = newline_break + 1
                
                end = best_break
            
            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "chunk_index": len(chunks),
                    "chunk_method": "recursive_character",
                    "metadata": {
                        **(metadata or {}),
                        "start_pos": start,
                        "end_pos": end
                    }
                })
            
            # 使用重叠移动起始位置
            start = end - self.chunk_overlap
            if start < 0:
                start = 0
        
        return chunks


class AgnoMarkdownChunker(BaseChunker):
    """使用Agno官方的MarkdownChunking进行文档切分。"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """初始化Markdown切分器。"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if not AGNO_AVAILABLE:
            logger.warning("Agno框架不可用，将使用fallback方法")
            self._fallback_chunker = RecursiveCharacterChunker(chunk_size, chunk_overlap)
        else:
            self._fallback_chunker = None
    
    def chunk(self, content: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        使用Agno的MarkdownChunking进行Markdown文档切分。
        
        基于文档结构（标题、段落、章节）进行智能分块。
        
        返回格式: List[Dict[str, Any]]，每个dict包含 'content' 和 'metadata' 字段
        """
        if not content:
            return []
        
        # 如果Agno不可用，使用fallback方法
        if not AGNO_AVAILABLE:
            logger.warning("Agno框架不可用，使用fallback递归切分方法")
            if self._fallback_chunker:
                return self._fallback_chunker.chunk(content, metadata)
            else:
                fallback = RecursiveCharacterChunker(self.chunk_size, self.chunk_overlap)
                return fallback.chunk(content, metadata)
        
        try:
            # 初始化MarkdownChunking策略
            chunking_strategy = MarkdownChunking(
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap
            )
            
            # 创建Document对象（chunk方法需要Document对象，而不是字符串）
            document = Document(content=content)
            
            # 使用chunk方法切分文档
            # MarkdownChunking的chunk方法返回Document对象列表
            chunk_objects = chunking_strategy.chunk(document)
            
            # 转换为标准格式
            chunks = []
            for i, chunk_obj in enumerate(chunk_objects):
                # 提取chunk内容
                chunk_content = ""
                if hasattr(chunk_obj, 'content'):
                    chunk_content = chunk_obj.content or ""
                elif hasattr(chunk_obj, 'text'):
                    chunk_content = chunk_obj.text or ""
                elif isinstance(chunk_obj, str):
                    chunk_content = chunk_obj
                else:
                    # 尝试获取其他可能的属性
                    chunk_content = str(chunk_obj)
                
                # 只跳过完全为空的内容，不进行长度限制
                if not chunk_content or not chunk_content.strip():
                    continue
                
                # 提取图片信息
                images = extract_images_from_text(chunk_content)
                
                # 提取结构信息
                structure = extract_structure_info(chunk_content)
                
                # 提取标题信息
                heading_match = re.search(r'^(#{1,6})\s+(.+)', chunk_content, re.MULTILINE)
                if heading_match:
                    heading_level = len(heading_match.group(1))
                    heading_text = heading_match.group(2).strip()
                else:
                    heading_level = 0
                    heading_text = ""
                
                # 构建metadata字典（保持与原有格式兼容）
                chunk_metadata = {
                    "chunk_index": i,
                    "chunk_method": "markdown_chunking",
                    "heading": heading_text,
                    "heading_level": heading_level,
                    "images": images,
                    "structure": structure,
                    "type": "markdown_chunk",
                    "split_method": "markdown_chunking"
                }
                
                # 如果chunk有metadata属性，合并进去
                if hasattr(chunk_obj, 'metadata') and chunk_obj.metadata:
                    if isinstance(chunk_obj.metadata, dict):
                        chunk_metadata.update(chunk_obj.metadata)
                
                # 合并传入的metadata
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    "content": chunk_content,
                    "metadata": chunk_metadata
                })
            
            if chunks:
                logger.debug(f"使用MarkdownChunking切分文档，生成 {len(chunks)} 个chunks")
                return chunks
            else:
                logger.warning("MarkdownChunking未生成有效chunks，将使用fallback方法")
                if self._fallback_chunker:
                    return self._fallback_chunker.chunk(content, metadata)
                else:
                    fallback = RecursiveCharacterChunker(self.chunk_size, self.chunk_overlap)
                    return fallback.chunk(content, metadata)
                    
        except Exception as e:
            logger.error(f"使用MarkdownChunking切分文档时出错: {str(e)}", exc_info=True)
            # 出错时使用fallback方法
            logger.debug("使用fallback递归切分方法")
            if self._fallback_chunker:
                return self._fallback_chunker.chunk(content, metadata)
            else:
                fallback = RecursiveCharacterChunker(self.chunk_size, self.chunk_overlap)
                return fallback.chunk(content, metadata)


class SemanticChunker(BaseChunker):
    """将语义相关内容分组的语义切分器。"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """初始化语义切分器。"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # 目前回退到AgnoMarkdownChunker
        self.base_chunker = AgnoMarkdownChunker(chunk_size, chunk_overlap)
    
    def chunk(self, content: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """语义切分内容。"""
        # 目前使用AgnoMarkdownChunker作为基础
        # 在生产环境中，可以使用嵌入向量来分组相似内容
        chunks = self.base_chunker.chunk(content, metadata)
        
        # 更新切分方法
        for chunk in chunks:
            if isinstance(chunk.get("metadata"), dict):
                chunk["metadata"]["chunk_method"] = "semantic"
            else:
                chunk["metadata"] = {"chunk_method": "semantic"}
        
        return chunks


class ChunkerFactory:
    """创建切分器的工厂类。"""
    
    _chunkers = {
        "recursive": RecursiveCharacterChunker,  # 递归切分，按照句子或段落切分（fallback）
        "markdown": AgnoMarkdownChunker,  # 使用Agno官方的MarkdownChunking
        "semantic": SemanticChunker,  # 语义切分，目前使用AgnoMarkdownChunker作为基础
    }
    
    @classmethod
    def create_chunker(
        cls,
        method: str = "markdown",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> BaseChunker:
        """创建切分器实例。"""
        chunker_class = cls._chunkers.get(method.lower())
        if not chunker_class:
            raise ValueError(f"Unknown chunker method: {method}. Available: {list(cls._chunkers.keys())}")
        
        return chunker_class(chunk_size, chunk_overlap)
    
    @classmethod
    def list_methods(cls) -> List[str]:
        """列出可用的切分方法。"""
        return list(cls._chunkers.keys())
    
    @classmethod
    def is_agno_available(cls) -> bool:
        """检查Agno是否可用。"""
        return AGNO_AVAILABLE

