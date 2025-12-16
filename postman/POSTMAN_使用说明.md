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
        "session_id": "optional-session-id"
    }
    ```

- **查询问答（带会话）**: 带会话 ID 的查询，可以保持对话上下文

### 4. 系统信息
- **获取切分方法列表** (`GET /api/v1/chunkers`): 获取所有支持的切分方法
- **获取系统统计** (`GET /api/v1/stats`): 获取系统统计信息

### 5. 会话管理
- **获取会话历史** (`GET /api/v1/sessions/{session_id}/history`): 获取指定会话的历史记录
  - 需要设置 `session_id` 变量
  - 需要启用 `agent_db.enabled` 配置

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

4. **查询问答**
   - 运行 `POST /api/v1/query`
   - 输入问题，例如："文档的主要内容是什么？"
   - 查看返回的答案和来源

5. **查看系统统计**
   - 运行 `GET /api/v1/stats`
   - 查看向量数据库和文档统计信息

### 会话测试流程

1. **创建会话查询**
   - 运行 `POST /api/v1/query`，设置 `session_id` 为唯一值（如：`test-session-001`）
   - 发送第一个问题

2. **继续会话**
   - 使用相同的 `session_id` 发送后续问题
   - 系统会保持对话上下文

3. **查看会话历史**
   - 运行 `GET /api/v1/sessions/{session_id}/history`
   - 查看该会话的所有历史记录

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

### 4. 连接错误
- 检查 `base_url` 变量是否正确
- 确认服务器正在运行
- 检查防火墙和网络设置

## 注意事项

1. **文件上传**：只支持 Markdown 格式文件
2. **切分方法**：推荐使用 `markdown` 方法处理 Markdown 文档
3. **会话管理**：需要启用 `agent_db.enabled` 配置才能使用会话功能
4. **环境变量**：根据实际部署环境修改 `base_url`
5. **文档 ID**：删除文档操作不可逆，请谨慎操作

## 更多信息

详细 API 文档请参考项目 README.md 文件，或访问：
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

