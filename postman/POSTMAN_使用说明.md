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

### 3. RAG 查询
- **查询问答** (`POST /api/v1/query`): 向 RAG 系统提问
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
  - **参数说明**：
    - `question`: 用户问题（必填）
    - `top_k`: 检索的文档片段数量（可选，默认使用配置值）
    - `similarity_threshold`: 相似度阈值（可选，默认使用配置值）
    - `session_id`: 会话 ID（可选，用于会话持久化）
    - `user_id`: 用户 ID（可选，用于记忆功能，如果未提供则使用 session_id 或默认值）

- **查询问答（带会话和用户）**: 带会话 ID 和用户 ID 的查询，可以保持对话上下文和用户记忆

### 4. 系统信息
- **获取切分方法列表** (`GET /api/v1/chunkers`): 获取所有支持的切分方法
- **获取系统统计** (`GET /api/v1/stats`): 获取系统统计信息，包括：
  - 向量数据库统计
  - 文档数量
  - 环境信息
  - AgentDB 启用状态

### 5. 会话管理
- **获取会话历史** (`GET /api/v1/sessions/{session_id}/history`): 获取指定会话的历史记录
  - 需要设置 `session_id` 变量
  - 需要启用 `agent_db.enabled` 配置

### 6. 记忆管理
- **获取记忆功能状态** (`GET /api/v1/memory/status`): 获取记忆功能的启用状态和配置信息
  - 返回信息包括：
    - 数据库连接状态
    - 表创建状态
    - 记忆功能是否启用

- **清理用户记忆** (`POST /api/v1/memory/{user_id}/prune`): 清理指定用户的记忆，保留最近的 N 条
  - 需要设置 `user_id` 变量
  - 查询参数 `keep_count`: 保留的记忆数量（可选，默认 10）
  - 示例：`POST /api/v1/memory/user-001/prune?keep_count=10`

### 7. AgentOS
- **AgentOS 服务说明**: AgentOS 是基于 Agno AgentOS 的独立服务，挂载在 `/agentos` 路径下
  - 提供完整的 Agent 管理功能
  - 集成 MySQL 和 Milvus
  - 访问 API 文档：
    - Swagger UI: `http://127.0.0.1:8000/agentos/docs`
    - ReDoc: `http://127.0.0.1:8000/agentos/redoc`
  - **注意**：AgentOS 服务需要正确配置 MySQL 和 Milvus 才能正常工作

## 测试流程示例

### 完整测试流程

1. **检查系统状态**
   - 运行 `GET /health` 确保服务正常运行

2. **检查记忆功能状态**
   - 运行 `GET /api/v1/memory/status` 查看记忆功能是否启用

3. **上传文档**
   - 运行 `POST /api/v1/documents/upload`
   - 选择一个 Markdown 文件
   - 记录返回的 `document_id`

4. **查看文档列表**
   - 运行 `GET /api/v1/documents`
   - 确认文档已成功添加

5. **查询问答（带用户记忆）**
   - 运行 `POST /api/v1/query`
   - 设置 `user_id` 为唯一值（如：`user-001`）
   - 输入问题，例如："文档的主要内容是什么？"
   - 查看返回的答案和来源

6. **继续对话（利用记忆）**
   - 使用相同的 `user_id` 和 `session_id` 发送后续问题
   - 系统会利用之前的记忆来回答

7. **查看会话历史**
   - 运行 `GET /api/v1/sessions/{session_id}/history`
   - 查看该会话的所有历史记录

8. **查看系统统计**
   - 运行 `GET /api/v1/stats`
   - 查看向量数据库和文档统计信息

### 记忆功能测试流程

1. **检查记忆状态**
   - 运行 `GET /api/v1/memory/status`
   - 确认记忆功能已启用

2. **创建带用户 ID 的查询**
   - 运行 `POST /api/v1/query`，设置 `user_id` 为唯一值（如：`user-001`）
   - 发送第一个问题，例如："我的名字是张三，请记住"
   - 系统会记住这个信息

3. **验证记忆功能**
   - 使用相同的 `user_id` 发送新问题："我的名字是什么？"
   - 系统应该能够回答："你的名字是张三"

4. **清理用户记忆**
   - 运行 `POST /api/v1/memory/user-001/prune?keep_count=5`
   - 系统会保留最近的 5 条记忆，删除更早的记忆

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

### 3. 会话历史为空
- 确认配置文件中 `agent_db.enabled = true`
- 检查 MySQL 数据库连接是否正常
- 确认使用了正确的 `session_id`

### 4. 记忆功能不工作
- 确认配置文件中 `agent_db.enabled = true`
- 运行 `GET /api/v1/memory/status` 检查记忆功能状态
- 确保在查询时提供了 `user_id` 参数
- 检查 MySQL 数据库连接和表是否正常创建

### 5. AgentOS 服务不可用
- 检查 MySQL 和 Milvus 服务是否正常运行
- 查看应用启动日志，确认 AgentOS 初始化是否成功
- 如果初始化失败，主应用仍会继续运行，但 AgentOS 路由将不可用

### 6. 连接错误
- 检查 `base_url` 变量是否正确
- 确认服务器正在运行
- 检查防火墙和网络设置

## 注意事项

1. **文件上传**：只支持 Markdown 格式文件
2. **切分方法**：推荐使用 `markdown` 方法处理 Markdown 文档
3. **会话管理**：需要启用 `agent_db.enabled` 配置才能使用会话功能
4. **记忆功能**：
   - 需要启用 `agent_db.enabled` 配置
   - 必须在查询时提供 `user_id` 参数才能启用记忆功能
   - 记忆数据存储在 MySQL 数据库中
5. **环境变量**：根据实际部署环境修改 `base_url`
6. **文档 ID**：删除文档操作不可逆，请谨慎操作
7. **用户 ID**：建议使用有意义的用户 ID，便于管理和追踪
8. **记忆清理**：定期清理用户记忆可以避免数据过多，建议根据实际需求设置 `keep_count` 参数

## 更多信息

详细 API 文档请参考项目 README.md 文件，或访问：
- **主应用 API 文档**：
  - Swagger UI: `http://127.0.0.1:8000/docs`
  - ReDoc: `http://127.0.0.1:8000/redoc`
- **AgentOS API 文档**（如果服务正常）：
  - Swagger UI: `http://127.0.0.1:8000/agentos/docs`
  - ReDoc: `http://127.0.0.1:8000/agentos/redoc`
