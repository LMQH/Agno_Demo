# Postman 接口测试使用说明

## 导入集合

1. 打开 Postman 应用
2. 点击左上角的 **Import** 按钮
3. 选择 `Agno_RAG_System.postman_collection.json` 文件
4. 点击 **Import** 完成导入

## 配置环境变量

集合中已预定义了以下变量，你可以根据需要修改：

- `base_url`: API 服务器地址（默认：`http://127.0.0.1:8000`）
- `document_id`: 文档 ID（用于测试文档相关接口）
- `session_id`: 会话 ID（用于测试会话相关接口）
- `user_id`: 用户 ID（用于测试记忆功能相关接口）

### 修改环境变量

1. 在 Postman 中，点击集合名称右侧的 **...** 菜单
2. 选择 **Edit**
3. 切换到 **Variables** 标签
4. 修改变量值并保存

## 系统架构说明

本系统采用**多智能体架构**，查询处理流程如下：

1. **Planning 智能体**：分析问题，判断处理路径
   - `direct`: 直接回答（简单问题）
   - `rag_only`: 仅检索后回答（需要知识库支持）
   - `multi_agent_debate`: 多立场讨论（复杂问题）
   - `reject`: 拒绝处理（违反安全策略）

2. **RAG 智能体**：从知识库检索相关文档片段（仅检索，不生成答案）

3. **讨论团队**（可选）：多立场讨论
   - 激进派 Agent
   - 保守派 Agent
   - 官方叙事 Agent
   - Leader 协调讨论

4. **判断智能体**：评估讨论质量，决定是否继续、终止或重新检索

5. **Reply 智能体**：整合所有信息，生成结构化最终答案

## 接口分组说明

### 1. 健康检查
- **根路径健康检查** (`GET /`): 检查系统是否正常运行
- **健康检查端点** (`GET /health`): 获取系统状态信息

### 2. 知识库管理
- **上传文档** (`POST /api/v1/documents/upload`): 上传 Markdown 文件到知识库
  - 需要选择文件（form-data 格式）
  - 可选择切分方法（recursive、markdown、semantic）
  
- **添加文档（文件路径）** (`POST /api/v1/documents/add`): 通过服务器本地路径添加文档
  - 请求体示例：
    ```json
    {
        "file_path": "/path/to/document.md",
        "chunk_method": "markdown"
    }
    ```

- **列出所有文档** (`GET /api/v1/documents`): 获取所有文档列表

- **获取文档详情** (`GET /api/v1/documents/{document_id}`): 获取指定文档的详细信息
  - 需要设置 `document_id` 变量

- **删除文档** (`DELETE /api/v1/documents/{document_id}`): 删除指定文档
  - 需要设置 `document_id` 变量

### 3. RAG 查询（多智能体架构）

- **查询问答** (`POST /api/v1/query`): 向多智能体 RAG 系统提问
  - 请求体示例：
    ```json
    {
        "question": "文档中提到了什么内容？",
        "top_k": 5,
        "similarity_threshold": 0.7,
        "session_id": "optional-session-id",
        "user_id": "optional-user-id"
    }
    ```
  - **请求参数说明**：
    - `question`: 用户问题（必填）
    - `top_k`: 检索的文档片段数量（可选，默认使用配置值）
    - `similarity_threshold`: 相似度阈值（可选，默认使用配置值）
    - `session_id`: 会话 ID（可选，用于会话持久化）
    - `user_id`: 用户 ID（可选，用于记忆功能，如果未提供则使用 session_id 或默认值）
  
  - **响应字段说明**：
    - `question`: 原始问题
    - `answer`: 最终答案（由 Reply 智能体生成）
    - `sources`: 检索到的文档片段列表
    - `num_sources`: 文档片段数量
    - `session_id`: 会话 ID
    - `processing_path`: 处理路径（`direct`、`rag_only`、`multi_agent_debate`、`reject`）
    - `plan`: 规划结果（包含复杂度、风险等级、是否需要检索等信息）
    - `debate_result`: 讨论结果（如果进行了讨论，包含讨论摘要和轮次）
    - `judgment_result`: 判断结果（如果进行了讨论，包含判断动作、理由、问题、改进建议）

- **查询问答（带会话和用户）**: 带会话 ID 和用户 ID 的查询，可以保持对话上下文和用户记忆

### 4. 系统信息
- **获取切分方法列表** (`GET /api/v1/chunkers`): 获取所有支持的切分方法
- **获取系统统计** (`GET /api/v1/stats`): 获取系统统计信息，包括：
  - 向量数据库统计
  - 文档数量
  - 环境信息
  - AgentDB 启用状态

### 5. AgentOS
- **AgentOS 服务说明**: AgentOS 是基于 Agno AgentOS 的独立服务，挂载在 `/agentos` 路径下
  - 提供完整的 Agent 管理功能
  - 集成 MySQL 和 Milvus
  - 访问 API 文档：
    - Swagger UI: `http://127.0.0.1:8000/agentos/docs`
    - ReDoc: `http://127.0.0.1:8000/agentos/redoc`
  - **注意**：AgentOS 服务需要正确配置 MySQL 和 Milvus 才能正常工作

## 重要变更说明

### 已移除的端点

以下端点已从 API 中移除，功能已由 WorkflowController 内部处理：

- ~~`GET /api/v1/sessions/{session_id}/history`~~ - 会话历史由 Agno 框架自动管理
- ~~`GET /api/v1/memory/status`~~ - 记忆功能由 WorkflowController 中的各个 Agent 管理
- ~~`POST /api/v1/memory/{user_id}/prune`~~ - 记忆管理由 Agno 框架自动处理

如果需要这些功能，可以通过 WorkflowController 或直接访问数据库实现。

## 测试流程示例

### 完整测试流程

1. **检查系统状态**
   - 运行 `GET /health` 确保服务正常运行

2. **上传文档**
   - 运行 `POST /api/v1/documents/upload`
   - 选择一个 Markdown 文件
   - 记录返回的 `document_id`

3. **查看文档列表**
   - 运行 `GET /api/v1/documents`
   - 确认文档已成功添加

4. **查询问答（简单问题）**
   - 运行 `POST /api/v1/query`
   - 设置 `user_id` 为唯一值（如：`user-001`）
   - 输入简单问题，例如："文档的主要内容是什么？"
   - 查看返回的答案和来源
   - 注意 `processing_path` 可能是 `direct` 或 `rag_only`

5. **查询问答（复杂问题，触发多智能体讨论）**
   - 运行 `POST /api/v1/query`
   - 使用相同的 `user_id` 和 `session_id`
   - 输入复杂或有争议的问题，例如："这个政策的影响是什么？"
   - 查看返回结果：
     - `processing_path` 可能是 `multi_agent_debate`
     - `debate_result` 包含多立场讨论结果
     - `judgment_result` 包含判断智能体的评估
     - `plan` 包含规划信息

6. **继续对话（利用记忆）**
   - 使用相同的 `user_id` 和 `session_id` 发送后续问题
   - 系统会利用之前的记忆和上下文来回答

7. **查看系统统计**
   - 运行 `GET /api/v1/stats`
   - 查看向量数据库和文档统计信息

### 多智能体架构测试流程

1. **测试简单问题（直接回答）**
   - 发送简单问题，如："你好"
   - 查看 `processing_path` 为 `direct`
   - 查看 `plan` 了解规划决策

2. **测试知识库检索（RAG）**
   - 发送需要知识库支持的问题
   - 查看 `processing_path` 为 `rag_only`
   - 查看 `sources` 包含检索到的文档片段

3. **测试多立场讨论**
   - 发送复杂或有争议的问题
   - 查看 `processing_path` 为 `multi_agent_debate`
   - 查看 `debate_result` 了解各立场观点
   - 查看 `judgment_result` 了解判断智能体的评估

4. **测试拒绝处理**
   - 发送违反安全策略的问题
   - 查看 `processing_path` 为 `reject`
   - 查看 `answer` 中的拒绝原因

### AgentOS 测试流程

1. **检查 AgentOS 服务**
   - 访问 `GET /agentos` 或直接访问 `http://127.0.0.1:8000/agentos/docs`
   - 如果服务正常，会显示 AgentOS 的 API 文档

2. **使用 AgentOS API**
   - 根据 AgentOS 的 API 文档进行测试
   - AgentOS 提供了独立的 Agent 管理功能

## 常见问题

### 1. 上传文件失败
- 确保文件是 Markdown 格式（`.md` 或 `.markdown`）
- 检查文件大小是否过大
- 确认服务器有足够的存储空间

### 2. 查询返回空结果
- 确保知识库中已有文档
- 检查 `similarity_threshold` 设置是否过高
- 尝试调整 `top_k` 参数

### 3. 没有触发多智能体讨论
- 多智能体讨论由 Planning 智能体根据问题复杂度自动决定
- 简单问题可能直接回答（`processing_path: direct`）
- 复杂或有争议的问题更可能触发讨论（`processing_path: multi_agent_debate`）

### 4. 记忆功能不工作
- 确认配置文件中 `agent_db.enabled = true`
- 确保在查询时提供了 `user_id` 参数
- 检查 MySQL 数据库连接和表是否正常创建
- 记忆功能由 WorkflowController 中的各个 Agent 自动管理

### 5. AgentOS 服务不可用
- 检查 MySQL 和 Milvus 服务是否正常运行
- 查看应用启动日志，确认 AgentOS 初始化是否成功
- 如果初始化失败，主应用仍会继续运行，但 AgentOS 路由将不可用

### 6. 连接错误
- 检查 `base_url` 变量是否正确
- 确认服务器正在运行
- 检查防火墙和网络设置

### 7. 响应中没有 debate_result 或 judgment_result
- 这些字段只在 `processing_path` 为 `multi_agent_debate` 时出现
- 简单问题可能不会触发讨论流程

## 注意事项

1. **文件上传**：只支持 Markdown 格式文件
2. **切分方法**：推荐使用 `markdown` 方法处理 Markdown 文档
3. **会话管理**：需要启用 `agent_db.enabled` 配置才能使用会话功能
4. **记忆功能**：
   - 需要启用 `agent_db.enabled` 配置
   - 必须在查询时提供 `user_id` 参数才能启用记忆功能
   - 记忆数据存储在 MySQL 数据库中
   - 由 WorkflowController 中的各个 Agent 自动管理
5. **环境变量**：根据实际部署环境修改 `base_url`
6. **文档 ID**：删除文档操作不可逆，请谨慎操作
7. **用户 ID**：建议使用有意义的用户 ID，便于管理和追踪
8. **多智能体架构**：
   - 系统会根据问题复杂度自动选择处理路径
   - 复杂问题可能触发多立场讨论，响应时间可能较长
   - 查看 `processing_path` 了解实际使用的处理路径
   - 查看 `plan`、`debate_result`、`judgment_result` 了解详细处理信息

## 响应示例

### 简单问题响应
```json
{
    "question": "你好",
    "answer": "你好！有什么可以帮助你的吗？",
    "sources": [],
    "num_sources": 0,
    "session_id": "session-123",
    "processing_path": "direct",
    "plan": {
        "processing_path": "direct",
        "complexity_level": "low",
        "risk_level": "low",
        "requires_retrieval": false
    },
    "debate_result": null,
    "judgment_result": null
}
```

### 复杂问题响应（多智能体讨论）
```json
{
    "question": "这个政策的影响是什么？",
    "answer": "根据多立场讨论，以下是结构化分析：\n\n1. 事实共识：...\n2. 立场分歧：...\n3. 不确定性与未来变量：...",
    "sources": [
        {
            "file_id": 1,
            "file_name": "policy.md",
            "content": "...",
            "score": 0.85
        }
    ],
    "num_sources": 1,
    "session_id": "session-123",
    "processing_path": "multi_agent_debate",
    "plan": {
        "processing_path": "multi_agent_debate",
        "complexity_level": "high",
        "risk_level": "medium",
        "requires_retrieval": true
    },
    "debate_result": {
        "question": "这个政策的影响是什么？",
        "summary": "讨论摘要...",
        "round": 2
    },
    "judgment_result": {
        "action": "terminate",
        "reasoning": "讨论已充分，各立场已表达核心观点",
        "issues": [],
        "improvements": []
    }
}
```

## 更多信息

详细 API 文档请参考项目 README.md 文件，或访问：
- **主应用 API 文档**：
  - Swagger UI: `http://127.0.0.1:8000/docs`
  - ReDoc: `http://127.0.0.1:8000/redoc`
- **AgentOS API 文档**（如果服务正常）：
  - Swagger UI: `http://127.0.0.1:8000/agentos/docs`
  - ReDoc: `http://127.0.0.1:8000/agentos/redoc`
