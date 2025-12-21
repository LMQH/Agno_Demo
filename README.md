# Agno RAG System

基于 Agno 框架的单智能体 RAG（检索增强生成）系统，支持知识库构建、向量检索和智能问答。

## 项目概述

本项目是一个完整的 RAG 系统实现，采用 `src-layout` 项目结构，所有源代码位于 `src/agno_project/` 目录下。系统支持 Markdown 格式文档的知识库构建，使用多种切分方法，并将文档存储到向量数据库中进行语义检索。

**项目状态：✅ 已完成并可用**

## 功能特性

- ✅ **知识库构建**：支持 Markdown 格式文档导入，提供多种文档切分方法
- ✅ **向量存储**：使用 Milvus 向量数据库存储文档嵌入向量
- ✅ **元数据管理**：使用 MySQL 存储文档和切片的元数据信息
- ✅ **RAG 检索**：基于语义相似度的文档检索
- ✅ **智能问答**：集成自定义 LLM 模型进行问答生成
- ✅ **会话管理**：支持多会话持久化，可查询会话历史记录
- ✅ **多环境配置**：支持 dev、show、prod 三个环境的独立配置
- ✅ **RESTful API**：提供完整的 FastAPI 接口，支持 Postman 测试
- ✅ **Agno 集成**：基于 Agno Agent 框架，支持工具调用和会话管理
- ✅ **AgentOS 支持**：提供基于 Agno AgentOS 的独立服务，支持 MySQL 和 Milvus 集成

## 技术栈

- **框架**：FastAPI、Agno
- **数据库**：MySQL（元数据）、Milvus（向量数据库）
- **嵌入模型**：text-embedding-v4（通义千问，兼容 OpenAI API）
- **推理模型**：deepseek-v3.2-exp（自定义私有模型）
- **配置管理**：TOML 格式配置文件
- **项目结构**：src-layout
- **会话管理**：基于 Agno PostgresDb 的会话持久化（使用 MySQL 存储）

## 项目结构

```
Agno_Agent/
├── config/                 # 环境配置文件
│   ├── dev.toml           # 开发环境配置（Windows）
│   ├── show.toml          # 测试环境配置（Linux）
│   └── prod.toml          # 生产环境配置（Linux）
├── src/
│   └── agno_project/      # 源代码目录
│       ├── api/           # FastAPI 应用和路由
│       │   ├── main.py    # 主应用和路由定义
│       │   └── run.py     # 运行入口
│       ├── config.py      # 配置管理
│       ├── database/      # 数据库客户端
│       │   ├── mysql_client.py    # MySQL 客户端
│       │   ├── milvus_client.py    # Milvus 向量数据库客户端
│       │   └── base.py            # 数据库基类接口
│       ├── knowledge_base/ # 知识库构建模块
│       │   ├── chunkers.py    # 文档切分器（支持多种切分方法）
│       │   ├── embedder.py    # 嵌入向量生成
│       │   └── builder.py     # 知识库构建器
│       ├── rag/           # RAG 检索和生成
│       │   ├── retriever.py   # 检索器
│       │   ├── llm_client.py  # LLM 客户端
│       │   ├── custom_model.py  # 自定义模型类（Agno Model 实现）
│       │   ├── tools.py       # RAG 工具（检索工具）
│       │   └── agent.py       # RAG 智能体（基于 Agno Agent）
│       ├── agentos/        # AgentOS 应用模块
│       │   ├── __init__.py
│       │   └── setup.py    # AgentOS 初始化模块（集成到主应用）
│       └── utils/         # 工具函数（预留目录）
├── pyproject.toml                    # 项目依赖配置
├── start.sh                          # Linux 启动脚本（可选）
├── Agno_RAG_System.postman_collection.json  # Postman 接口测试集合
├── POSTMAN_使用说明.md                # Postman 使用说明文档
└── README.md                         # 项目文档
```

## 环境要求

- Python >= 3.9
- MySQL >= 5.7
- Milvus >= 2.3.0
- 通义千问 API Key（用于生成嵌入向量，兼容 OpenAI API）
- 自定义 LLM API（deepseek-v3.2-exp）

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd Agno_Agent
```

### 2. 创建虚拟环境

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -e .
```

或者使用生成的 requirements.txt：
```bash
pip install -r requirements.txt
```

### 4. 配置数据库

#### MySQL 配置

创建数据库：
```sql
CREATE DATABASE agno_rag_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### Milvus 配置

确保 Milvus 服务正在运行：
```bash
# 使用 Docker 启动 Milvus
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest
```

### 5. 配置环境变量和 API

编辑对应环境的配置文件（`config/dev.toml`、`config/show.toml` 或 `config/prod.toml`）：

```toml
[model.embedding]
provider = "qwen-embedding"
model_name = "text-embedding-v4"
api_key = "your-qwen-api-key"
api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
dimension = 1024

[model.llm]
provider = "custom"
model_name = "deepseek-v3.2-exp"
api_base = "your-llm-api-endpoint"
api_key = "your-llm-api-key"
temperature = 0.7
max_tokens = 5000

[agent_db]
enabled = true  # 启用会话持久化
```

## 启动服务

### 使用 uvicorn 启动（推荐，所有平台通用）

首先确保已安装项目依赖：

```bash
# 安装项目依赖
pip install -e .
```

然后使用 uvicorn 启动服务：

**Linux/macOS:**
```bash
# 设置环境变量
export ENVIRONMENT=dev  # 或 show、prod

# 启动服务
python -m uvicorn agno_project.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Windows:**
```cmd
# 设置环境变量
set ENVIRONMENT=dev

# 启动服务
python -m uvicorn agno_project.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 使用启动脚本（Linux 可选）

如果使用 Linux 环境，也可以使用提供的启动脚本：

```bash
# 设置环境变量
export ENVIRONMENT=show  # 或 prod

# 赋予执行权限
chmod +x start.sh

# 启动服务
./start.sh
```

### 启动参数说明

- `--host`: 服务监听地址（默认：127.0.0.1，生产环境建议使用 0.0.0.0）
- `--port`: 服务端口（默认：8000）
- `--reload`: 开发模式，代码变更自动重载（生产环境建议移除）

服务启动后，访问 `http://localhost:8000` 查看 API 文档。

### AgentOS 集成

AgentOS 已集成到主 FastAPI 应用中，无需单独启动。AgentOS 的路由已挂载到 `/agentos` 路径下。

**访问地址：** `http://localhost:8000/agentos`

**功能特性：**
- 使用 MySQL 进行会话持久化
- 使用 Milvus 作为知识库向量数据库
- 支持从配置文件读取模型和数据库配置
- 自动启用知识库搜索和上下文添加
- 与主应用共享配置和资源

**注意：** AgentOS 会在主应用启动时自动初始化，如果初始化失败，主应用会继续运行并记录警告日志。

## API 接口文档

### 健康检查

- **GET** `/` - 根路径健康检查
- **GET** `/health` - 健康检查端点

### 知识库管理

#### 上传文档

- **POST** `/api/v1/documents/upload`
  - 请求：`multipart/form-data`
    - `file`: Markdown 文件
    - `chunk_method`: 切分方法（可选，默认：markdown）
  - 响应：
    ```json
    {
      "document_id": 1,
      "status": "success",
      "chunks_count": 10
    }
    ```

#### 添加文档（通过文件路径）

- **POST** `/api/v1/documents/add`
  - 请求：JSON
    ```json
    {
      "file_path": "/path/to/document.md",
      "chunk_method": "markdown"
    }
    ```

#### 列出所有文档

- **GET** `/api/v1/documents`
  - 响应：文档列表

#### 获取文档详情

- **GET** `/api/v1/documents/{document_id}`
  - 响应：文档详细信息

#### 删除文档

- **DELETE** `/api/v1/documents/{document_id}`
  - 响应：删除结果

### RAG 查询

#### 查询问答

- **POST** `/api/v1/query`
  - 请求：
    ```json
    {
      "question": "你的问题",
      "top_k": 5,
      "similarity_threshold": 0.7,
      "session_id": "optional-session-id"
    }
    ```
  - 响应：
    ```json
    {
      "question": "你的问题",
      "answer": "AI 生成的答案",
      "sources": [
        {
          "tool": "rag_retrieval",
          "query": "你的问题"
        }
      ],
      "num_sources": 1,
      "session_id": "session-id"
    }
    ```

### 系统信息

#### 获取切分方法列表

- **GET** `/api/v1/chunkers`
  - 响应：可用的切分方法列表

#### 获取系统统计

- **GET** `/api/v1/stats`
  - 响应：系统统计信息（向量数据库统计、文档数量、环境信息等）

### 会话管理

#### 获取会话历史

- **GET** `/api/v1/sessions/{session_id}/history`
  - 响应：指定会话的历史记录
    ```json
    {
      "session_id": "session-id",
      "history": [...],
      "message_count": 10
    }
    ```

## 文档切分方法

系统支持以下文档切分方法：

1. **recursive** - 递归字符切分（默认）
   - 按字符数切分，尝试在句子边界处断开
   - 适合通用文档

2. **markdown** - Markdown 感知切分
   - 尊重 Markdown 文档结构（标题、段落）
   - 优先在章节边界处切分
   - 适合 Markdown 格式文档

3. **semantic** - 语义切分
   - 基于语义相似度分组
   - 适合需要保持语义连贯性的场景

## 环境配置说明

### 开发环境（dev）

- 环境：Windows
- 配置：`config/dev.toml`
- 特点：调试模式开启，本地数据库

### 测试环境（show）

- 环境：Linux
- 配置：`config/show.toml`
- 特点：调试模式开启，测试数据库

### 生产环境（prod）

- 环境：Linux
- 配置：`config/prod.toml`
- 特点：调试模式关闭，生产数据库，连接池优化

## 使用示例

### 使用 Postman 测试

项目提供了完整的 Postman 接口测试集合，可以直接导入使用：

1. **导入 Postman 集合**
   - 打开 Postman 应用
   - 点击 **Import** 按钮
   - 选择项目根目录下的 `Agno_RAG_System.postman_collection.json` 文件
   - 导入后即可看到所有接口，已按功能分组

2. **配置环境变量**
   - 集合中已预定义 `base_url` 变量（默认：`http://127.0.0.1:8000`）
   - 可根据实际部署环境修改

3. **快速测试**
   - **上传文档**：在"知识库管理"分组中选择"上传文档"，选择 Markdown 文件并发送
   - **查询问答**：在"RAG 查询"分组中选择"查询问答"，输入问题并发送
   - **查看文档列表**：在"知识库管理"分组中选择"列出所有文档"

详细使用说明请参考 `POSTMAN_使用说明.md` 文件。

### 手动测试示例

1. **上传文档**
   - Method: POST
   - URL: `http://localhost:8000/api/v1/documents/upload`
   - Body: form-data
     - Key: `file`, Type: File, Value: 选择 Markdown 文件
     - Key: `chunk_method`, Type: Text, Value: `markdown`

2. **查询问答**
   - Method: POST
   - URL: `http://localhost:8000/api/v1/query`
   - Body: raw JSON
     ```json
     {
       "question": "文档中提到了什么内容？",
       "top_k": 5
     }
     ```

3. **查看文档列表**
   - Method: GET
   - URL: `http://localhost:8000/api/v1/documents`

### Python 代码示例

#### RAG 系统使用示例

```python
import asyncio
from agno_project.knowledge_base.builder import KnowledgeBaseBuilder
from agno_project.rag.agent import RAGAgent

async def main():
    # 构建知识库
    builder = KnowledgeBaseBuilder()
    result = await builder.add_document(
        file_path="example.md",
        chunk_method="markdown"
    )
    print(f"文档已添加: {result}")
    
    # RAG 查询
    agent = RAGAgent()
    response = await agent.query("你的问题")
    print(f"答案: {response['answer']}")
    print(f"来源: {response['sources']}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### AgentOS 使用示例

AgentOS 已集成到主应用中，可以通过主应用的 `/agentos` 路径访问：

```python
import requests

# 主应用地址（AgentOS 挂载在 /agentos 路径下）
base_url = "http://localhost:8000/agentos"

# 发送消息给 Agent
response = requests.post(
    f"{base_url}/chat",
    json={
        "message": "你好，请介绍一下知识库的功能",
        "session_id": "user-123"  # 可选，用于会话持久化
    }
)

print(response.json())
```

## 注意事项

1. **API 密钥配置**：确保在配置文件中正确设置通义千问 API Key 和自定义 LLM API 地址
2. **数据库连接**：确保 MySQL 和 Milvus 服务正常运行
3. **文件编码**：Markdown 文件应使用 UTF-8 编码
4. **向量维度**：确保嵌入模型的维度与 Milvus 配置中的维度一致（默认 1024）
5. **环境变量**：启动前设置 `ENVIRONMENT` 环境变量以选择配置文件
6. **会话持久化**：如果启用了 `agent_db.enabled`，Agno 会在 MySQL 中自动创建会话管理表
7. **依赖安装**：首次运行前请确保安装所有依赖，建议使用虚拟环境
8. **AgentOS 配置**：AgentOS 已集成到主应用中，会自动从 `config/dev.toml` 读取 MySQL 和 Milvus 配置，确保配置文件正确设置
9. **端口冲突**：主应用使用 8000 端口，AgentOS 路由挂载在 `/agentos` 路径下，无需单独端口

## 开发说明

### 添加新的切分方法

1. 在 `src/agno_project/knowledge_base/chunkers.py` 中创建新的切分器类
2. 继承 `BaseChunker` 并实现 `chunk` 方法
3. 在 `ChunkerFactory` 中注册新方法

### 扩展数据库支持

1. 实现 `VectorStoreInterface` 或 `DocumentStoreInterface`（位于 `database/base.py`）
2. 在配置文件中添加新的数据库配置项
3. 更新 `KnowledgeBaseBuilder` 以支持新数据库

### 自定义切分方法

1. 在 `src/agno_project/knowledge_base/chunkers.py` 中创建新的切分器类
2. 继承 `BaseChunker` 并实现 `chunk` 方法
3. 在 `ChunkerFactory` 中注册新方法

## 故障排查

### 常见问题

1. **导入错误**：确保已安装所有依赖，并且 Python 路径正确。使用 `pip install -e .` 安装项目
2. **数据库连接失败**：检查数据库服务状态和配置信息，确保 MySQL 和 Milvus 服务正常运行
3. **嵌入生成失败**：验证通义千问 API Key 和网络连接，检查 `api_base` 配置是否正确
4. **LLM 调用失败**：检查自定义 LLM API 地址和密钥配置
5. **会话管理错误**：如果启用了 `agent_db.enabled`，确保 MySQL 数据库连接正常，Agno 会自动创建必要的表
6. **端口占用**：如果 8000 端口被占用，可以在配置文件中修改 `port` 配置

## 许可证

[根据项目实际情况填写]

## 联系方式

[根据项目实际情况填写]

