# 快速开始指南

## 5 分钟快速上手

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -e .
```

### 2. 配置数据库

#### MySQL
```sql
CREATE DATABASE agno_rag_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### Milvus（使用 Docker）
```bash
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest
```

### 3. 配置 API 密钥

编辑 `config/dev.toml`：

```toml
[model.embedding]
api_key = "sk-your-openai-api-key"

[model.llm]
api_base = "http://your-llm-api-endpoint/v1/chat/completions"
api_key = "your-llm-api-key"
```

### 4. 启动服务

**使用 uvicorn 启动（推荐，所有平台通用）：**

```bash
# Windows
set ENVIRONMENT=dev
python -m uvicorn agno_project.api.main:app --host 127.0.0.1 --port 8000 --reload

# Linux/macOS
export ENVIRONMENT=dev  # 或 show、prod
python -m uvicorn agno_project.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**或使用启动脚本（Linux 可选）：**

```bash
export ENVIRONMENT=show
chmod +x start.sh
./start.sh
```

### 5. 测试 API

访问 `http://localhost:8000/docs` 查看 API 文档。

#### 上传文档
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@example.md" \
  -F "chunk_method=markdown"
```

#### 查询问答
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "RAG 系统的工作原理是什么？",
    "top_k": 5
  }'
```

## 使用 Postman 测试

### 导入文档
1. Method: `POST`
2. URL: `http://localhost:8000/api/v1/documents/upload`
3. Body: `form-data`
   - Key: `file`, Type: `File`, Value: 选择 `example.md`
   - Key: `chunk_method`, Type: `Text`, Value: `markdown`

### 查询问答
1. Method: `POST`
2. URL: `http://localhost:8000/api/v1/query`
3. Body: `raw JSON`
```json
{
  "question": "RAG 系统的主要优势是什么？",
  "top_k": 5,
  "similarity_threshold": 0.7
}
```

## 常见问题

### Q: 启动时提示找不到配置文件？
A: 确保设置了 `ENVIRONMENT` 环境变量，并且对应的配置文件存在于 `config/` 目录。

### Q: 数据库连接失败？
A: 检查 MySQL 和 Milvus 服务是否运行，以及配置文件中的连接信息是否正确。

### Q: 嵌入生成失败？
A: 检查 OpenAI API Key 是否正确配置，以及网络连接是否正常。

### Q: LLM 调用失败？
A: 检查自定义 LLM API 地址和密钥配置，确保 API 端点格式正确。

## 下一步

- 阅读完整的 [README.md](README.md) 了解详细功能
- 查看 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 了解项目架构
- 探索 API 文档：`http://localhost:8000/docs`

