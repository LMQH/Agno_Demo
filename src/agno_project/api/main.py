"""FastAPI 主应用程序。"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import tempfile
import logging
import asyncio
from pathlib import Path
from agno.agent import RunOutput

from ..config import get_config
from ..knowledge_base.builder import KnowledgeBaseBuilder
from ..agents.capability.rag_agent import RAGAgent
from ..agentos import get_agent_os_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 初始化 FastAPI 应用
config = get_config()
app = FastAPI(
    title=config.name,
    description="RAG System based on Agno framework",
    version="0.1.0",
    debug=config.debug
)

# 配置日志
logger = logging.getLogger(__name__)

# 初始化组件
kb_builder = KnowledgeBaseBuilder()
rag_agent = RAGAgent()

# 集成 AgentOS
try:
    agent_os_app = get_agent_os_app()
    # 挂载 AgentOS 的路由到 /agentos 路径
    app.mount("/agentos", agent_os_app)
    logger.info("✓ AgentOS 已集成到主应用，路由挂载在 /agentos")
except Exception as e:
    logger.warning(f"AgentOS 集成失败，将继续运行主应用: {e}")


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化事件，用于初始化 Agno 数据库表。"""
    try:
        logger.debug("=" * 60)
        logger.debug("开始初始化 Agno 数据库表...")
        logger.debug("会话 ID: session_start")
        logger.debug("用户 ID: lmqh")
        
        # 触发一次简单的 Agent 调用来初始化数据库表
        # 这会让 Agno 自动创建必要的表（agno_memories, agno_runs 等）
        # 使用 agent.print_response() 方法，必须提供 user_id 才能启用记忆功能
        # 使用包含用户信息的对话来触发记忆写入，从而创建表

        # result = await rag_agent.query(
        #     question="你好，我是用户 lmqh，请记住我的名字。请用一句话简短回复（不超过30字）。",
        #     session_id="session_start",
        #     user_id="lmqh"  # 必须提供 user_id 才能启用记忆功能
        rag_agent.agent.print_response(
            "你好，我是用户 lmqh，请记住我的名字。请用一句话简短回复（不超过30字）。",
            user_id="lmqh",  # 必须提供 user_id 才能启用记忆功能
            session_id="session_start"
        )
        
        logger.debug("Agno 数据库表初始化成功")
        logger.debug("=" * 60)
    except Exception as e:
        # 初始化失败不影响应用启动，只记录警告
        logger.warning(f"Agno 数据库表初始化失败（将在首次使用时自动创建）: {e}")
        logger.warning("应用将继续启动，表将在首次成功调用时自动创建")


# 请求/响应模型
class QueryRequest(BaseModel):
    """查询请求模型。"""
    question: str
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None  # 用户 ID，用于记忆功能


class QueryResponse(BaseModel):
    """查询响应模型。"""
    question: str
    answer: str
    sources: List[dict]
    num_sources: int
    session_id: Optional[str] = None


class DocumentResponse(BaseModel):
    """文档响应模型。"""
    id: int
    file_name: str
    updated_at: Optional[str]


class AddDocumentResponse(BaseModel):
    """添加文档响应模型。"""
    document_id: int
    status: str
    chunks_count: Optional[int] = None
    message: Optional[str] = None


class DeleteDocumentResponse(BaseModel):
    """删除文档响应模型。"""
    document_id: int
    status: str
    chunks_deleted: int


class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str
    environment: str
    version: str


# 路由
@app.get("/", response_model=HealthResponse)
async def root():
    """根端点 - 健康检查。"""
    return {
        "status": "healthy",
        "environment": config.environment,
        "version": "0.1.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查端点。"""
    return {
        "status": "healthy",
        "environment": config.environment,
        "version": "0.1.0"
    }


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """查询 RAG 系统。"""
    try:
        # 使用 agent.run() 方法，必须提供 user_id 才能启用记忆功能
        # 如果没有提供 user_id，使用 session_id 或默认值
        user_id = request.user_id or request.session_id or "default_user"
        session_id = request.session_id
        
        # 调用 agent.run() 方法（同步版本，在异步环境中使用 asyncio.to_thread）
        # 参考官方示例：response: RunOutput = agent.run("你的问题")
        # 必须传递 user_id 和 session_id 才能启用记忆功能
        response: RunOutput = await asyncio.to_thread(
            rag_agent.agent.run,
            request.question,
            user_id=user_id,  # 必须提供 user_id 才能启用记忆功能
            session_id=session_id
        )
        
        # 按照官方示例，直接使用 response.content 获取答案
        answer = response.content
        
        # 使用统一的 sources 提取方法
        sources = rag_agent._extract_sources_from_response(response)
        
        # 如果仍然没有 sources，记录警告
        if not sources:
            logger.warning(f"查询 '{request.question}' 未返回 sources（Agent 可能未调用检索工具）")
        
        return {
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "num_sources": len(sources),
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@app.post("/api/v1/documents/upload", response_model=AddDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_method: str = Form(default="markdown")
):
    """上传并处理 Markdown 文档。"""
    if not file.filename.endswith(('.md', '.markdown')):
        raise HTTPException(status_code=400, detail="Only markdown files are supported")
    
    # 获取项目根目录下的 data/knowledge_base 目录
    project_root = Path(__file__).parent.parent.parent.parent
    temp_dir = project_root / "data" / "knowledge_base"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 优化：直接读取文件内容，避免先写临时文件再读取
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.debug(f"开始上传文件: {file.filename}")
        content_bytes = await file.read()
        content = content_bytes.decode('utf-8')
        content_size = len(content)
        logger.debug(f"文件读取完成: {file.filename}, 大小: {content_size} 字符")
        
        # 立即释放bytes内存
        del content_bytes
        
        # 生成临时文件路径（仅用于记录，实际不写入）
        # 添加upload_前缀以便builder识别并去掉
        tmp_path = str(temp_dir / f"upload_{file.filename}")
        
        # 直接传递内容，避免文件I/O
        result = await kb_builder.add_document(
            file_path=tmp_path,  # 仅用于生成文件名
            chunk_method=chunk_method,
            content=content  # 直接传递内容
        )
        
        # 释放content内存
        del content
        
        logger.info(f"文件上传并处理完成: {file.filename}, document_id={result.get('file_id')}")
        
        # 保持API兼容性，将file_id映射为document_id
        return {
            "document_id": result.get("file_id", result.get("document_id", 0)),
            "status": result["status"],
            "chunks_count": result.get("chunks_count", 0),
            "message": result.get("message")
        }
    except Exception as e:
        logger.error(f"文件上传处理失败: {file.filename}, 错误: {e}", exc_info=True)
        # 出错时也删除临时文件
        tmp_path = str(temp_dir / f"upload_{file.filename}")
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


class AddDocumentRequest(BaseModel):
    """添加文档请求模型。"""
    file_path: str
    chunk_method: str = "markdown"


@app.post("/api/v1/documents/add", response_model=AddDocumentResponse)
async def add_document(request: AddDocumentRequest):
    """从文件路径添加文档。"""
    try:
        result = await kb_builder.add_document(
            file_path=request.file_path,
            chunk_method=request.chunk_method
        )
        # 保持API兼容性，将file_id映射为document_id
        return {
            "document_id": result.get("file_id", result.get("document_id", 0)),
            "status": result["status"],
            "chunks_count": result.get("chunks_count", 0),
            "message": result.get("message")
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


@app.get("/api/v1/documents", response_model=List[DocumentResponse])
async def list_documents():
    """列出知识库中的所有文档。"""
    try:
        documents = kb_builder.list_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/api/v1/documents/{file_id}", response_model=DocumentResponse)
async def get_document(file_id: int):
    """根据 ID 获取文档。"""
    try:
        documents = kb_builder.list_documents()
        document = next((d for d in documents if d["id"] == file_id), None)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document not found: {file_id}")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.delete("/api/v1/documents/{file_id}", response_model=DeleteDocumentResponse)
async def delete_document(file_id: int):
    """从知识库中删除文档。"""
    try:
        result = kb_builder.delete_document(file_id)
        return {
            "document_id": result["file_id"],  # 保持API兼容性
            "status": result["status"],
            "chunks_deleted": 0  # 不再统计chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get("/api/v1/chunkers")
async def list_chunkers():
    """列出可用的切分方法。"""
    from ..knowledge_base.chunkers import ChunkerFactory
    methods = ChunkerFactory.list_methods()
    return {
        "methods": methods,
        "default": "markdown"
    }


@app.get("/api/v1/stats")
async def get_stats():
    """获取系统统计信息。"""
    try:
        stats = kb_builder.milvus_client.get_collection_stats()
        documents = kb_builder.list_documents()
        agent_db_enabled = config.agent_db.enabled if hasattr(config, 'agent_db') else False
        return {
            "vector_db": stats,
            "documents_count": len(documents),
            "environment": config.environment,
            "agent_db_enabled": agent_db_enabled
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@app.get("/api/v1/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """获取会话历史记录。"""
    try:
        history = rag_agent.get_session_history(session_id=session_id)
        return {
            "session_id": session_id,
            "history": history,
            "message_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话历史失败: {str(e)}")


@app.get("/api/v1/memory/status")
async def get_memory_status():
    """获取记忆功能状态。"""
    try:
        status = rag_agent.verify_memory_enabled()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆状态失败: {str(e)}")


@app.post("/api/v1/memory/{user_id}/prune")
async def prune_user_memory(user_id: str, keep_count: Optional[int] = None):
    """清理指定用户的记忆（保留最近的 N 条）。
    
    Args:
        user_id: 用户 ID
        keep_count: 保留的记忆数量，如果为 None 则使用默认值（10）
    """
    try:
        result = await rag_agent.prune_memories(user_id=user_id, keep_count=keep_count)
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理记忆失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import sys
    
    # 如果包未安装，添加 src 目录到路径
    try:
        import agno_project
    except ImportError:
        # 添加项目根目录的 src 到 Python 路径
        project_root = Path(__file__).parent.parent.parent.parent
        src_path = project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
    
    # 直接运行 app 对象（更可靠的方式）
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        reload=config.debug
    )

