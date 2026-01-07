# AgentOS 连接问题排查指南

## 问题：Failed to connect to the AgentOS

### 快速检查清单

1. **确认 AgentOS 已正确整合**
   - 启动主应用后，检查日志中是否有：
     ```
     ✓ AgentOS 已通过 base_app 方式整合到主应用（官方推荐）
     AgentOS 路由已通过 get_app() 注册到 base_app
     AgentOS 路由已添加到主应用中，共 X 个路由
     ```

2. **检查健康检查端点**
   ```bash
   # 访问健康检查端点
   curl http://localhost:8000/health
   ```
   应该返回 JSON 响应，包含 AgentOS 的健康状态。

3. **检查 AgentOS 状态 API**
   ```bash
   # 访问状态端点
   curl http://localhost:8000/api/v1/agentos/status
   ```
   检查返回的 JSON，确认：
   - `status`: "running"
   - `security_configured`: true（如果配置了安全密钥）
   - `endpoint_url`: 正确的端点 URL

4. **检查安全密钥配置**
   - 在 `config/dev.toml` 中确认 `os_security_key` 已配置
   - 安全密钥不能为空字符串
   - 安全密钥应该以 `sk-` 开头

5. **检查 Control Plane 端点 URL**
   - 在 Control Plane 中连接时，使用：`http://localhost:8000`
   - **不要**使用 `/agentos` 子路径（使用 base_app 整合后，路由直接添加到根路径）

### 常见问题及解决方案

#### 问题 1: AgentOS 路由未注册

**症状**: 访问 `/health` 或 AgentOS 相关端点返回 404

**解决方案**:
1. 确认 `get_agent_os_app(base_app=app)` 被调用
2. 确认 `agent_os.get_app()` 被调用（已在代码中修复）
3. 检查启动日志，确认看到 "AgentOS 路由已通过 get_app() 注册到 base_app"

#### 问题 2: 安全密钥未配置

**症状**: `security_configured: false`，Control Plane 无法连接

**解决方案**:
1. 访问 https://os.agno.com
2. 登录并进入组织设置
3. 生成安全密钥
4. 在 `config/dev.toml` 中设置：
   ```toml
   [agentos]
   os_security_key = "sk-your-key-here"
   ```
5. 重启应用

#### 问题 3: 端点 URL 配置错误

**症状**: Control Plane 显示连接失败

**解决方案**:
- **mounted 模式（base_app 整合）**: 使用 `http://localhost:8000`（主应用端口，无需子路径）
- **standalone 模式**: 使用 `http://localhost:7777`（AgentOS 独立端口）

#### 问题 4: CORS 问题

**症状**: 浏览器控制台显示 CORS 错误

**解决方案**:
1. 确认 CORS 中间件已配置
2. 检查 `allow_origins` 是否包含 `https://os.agno.com`
3. 开发环境可以临时允许所有来源（`["*"]`）

### 诊断步骤

#### 步骤 1: 检查应用启动日志

启动主应用后，应该看到：
```
开始整合 AgentOS 到主应用...
✓ AgentOS 路由已通过 get_app() 注册到 base_app
✓ AgentOS 已通过 base_app 方式整合到主应用（官方推荐）
  AgentOS 路由已添加到主应用中，共 X 个路由
  端点 URL: http://127.0.0.1:8000
  ✓ Control Plane 安全密钥已配置（如果已配置）
```

#### 步骤 2: 测试健康检查端点

```bash
curl http://localhost:8000/health
```

应该返回类似：
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "..."
}
```

#### 步骤 3: 检查 AgentOS 状态

```bash
curl http://localhost:8000/api/v1/agentos/status | python -m json.tool
```

检查关键字段：
- `status`: 应该是 "running"
- `run_mode`: 应该是 "mounted"
- `endpoint_url`: 应该是 "http://127.0.0.1:8000" 或 "http://localhost:8000"
- `security_configured`: 如果配置了安全密钥，应该是 true
- `control_plane_ready`: 如果配置了安全密钥，应该是 true

#### 步骤 4: 检查路由列表

访问 FastAPI 文档：
```
http://localhost:8000/docs
```

应该能看到 AgentOS 的路由，如：
- `/health` - 健康检查
- `/agents` - Agent 管理
- `/teams` - Team 管理
- `/workflows` - Workflow 管理
- 等等

#### 步骤 5: 在 Control Plane 中连接

1. 访问 https://os.agno.com
2. 登录并进入组织
3. 点击 "Add new OS"
4. 选择 "Local" 环境
5. **Endpoint URL**: `http://localhost:8000`（mounted 模式，无需子路径）
6. **OS Name**: 填写名称
7. 点击 "CONNECT"

### 调试技巧

#### 启用详细日志

在 `config/dev.toml` 中：
```toml
[app]
debug = true  # 启用调试模式
```

#### 检查 AgentOS 实例

在 Python 交互式环境中：
```python
from agno_project.agentos import create_agent_os
from agno_project.api.main import app

# 检查 AgentOS 是否已创建
agent_os = create_agent_os()
print(f"AgentOS ID: {agent_os.id}")
print(f"Agents: {len(agent_os.agents)}")

# 检查路由
print(f"Routes: {len(app.routes)}")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path}")
```

### 如果仍然无法连接

1. **检查防火墙**: 确保端口 8000 未被阻止
2. **检查端口占用**: 确保端口 8000 未被其他程序占用
3. **查看完整错误日志**: 检查应用启动时的完整日志输出
4. **尝试 standalone 模式**: 如果 mounted 模式有问题，可以尝试 standalone 模式
5. **联系支持**: 如果问题仍然存在，请提供完整的错误日志和配置信息

### 参考

- [AgentOS Control Plane 连接指南](./AgentOS_Control_Plane_连接指南.md)
- [Agno 官方文档](https://docs.agno.com)

