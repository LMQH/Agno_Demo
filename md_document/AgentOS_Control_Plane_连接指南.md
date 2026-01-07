# AgentOS Control Plane 连接指南

本文档详细说明如何将本地 AgentOS 实例连接到 Agno Control Plane (https://os.agno.com)，实现通过网页进行 Agent/Workflow 管理、会话历史查看、知识库管理和系统监控等功能。

## 目录

- [概述](#概述)
- [前置条件](#前置条件)
- [步骤 1: 在 Control Plane 创建账户](#步骤-1-在-control-plane-创建账户)
- [步骤 2: 获取安全密钥](#步骤-2-获取安全密钥)
- [步骤 3: 配置本地 AgentOS](#步骤-3-配置本地-agentos)
- [步骤 4: 启动应用](#步骤-4-启动应用)
- [步骤 5: 在 Control Plane 中连接](#步骤-5-在-control-plane-中连接)
- [步骤 6: 验证连接](#步骤-6-验证连接)
- [使用管理界面](#使用管理界面)
- [故障排除](#故障排除)
- [参考资源](#参考资源)

---

## 概述

AgentOS Control Plane 是 Agno 框架提供的网页管理界面，允许您：

- **Agent 管理**: 查看、测试和管理所有配置的 Agent
- **会话历史**: 查看和管理所有会话记录
- **知识库管理**: 上传、组织和搜索知识库文档
- **系统监控**: 查看系统状态、性能指标和使用统计
- **Workflow 管理**: 创建、编辑和测试 Workflow

### 架构

```
┌─────────────────┐
│  Control Plane  │
│  os.agno.com    │
└────────┬────────┘
         │ HTTPS + Bearer Token
         │
┌────────▼────────────────────────┐
│  Local AgentOS Instance         │
│  http://localhost:8000/agentos │
│  - FastAPI App                  │
│  - Agent Management             │
│  - Session Management           │
│  - Knowledge Base               │
└─────────────────────────────────┘
```

---

## 前置条件

1. **运行中的 AgentOS 实例**
   - 确保您的应用已正确配置并可以启动
   - AgentOS 已挂载在 `/agentos` 路径

2. **网络访问**
   - 本地开发：AgentOS 运行在 `localhost` 或 `127.0.0.1`
   - 生产环境：AgentOS 需要可通过 HTTPS 访问的公网地址

3. **配置文件**
   - 确保已配置 `config/dev.toml`（或相应环境的配置文件）

---

## 步骤 1: 在 Control Plane 创建账户

1. 访问 [Agno Control Plane](https://os.agno.com)
2. 注册新账户或登录现有账户
3. 创建或加入一个组织（Organization）

---

## 步骤 2: 获取安全密钥

安全密钥用于验证 Control Plane 与您的 AgentOS 实例之间的连接。

### 获取步骤

1. 登录 Control Plane
2. 点击顶部导航栏的组织/团队下拉菜单
3. 进入 **组织设置**（Organization Settings）
4. 找到 **安全密钥**（Security Keys）部分
5. 点击 **生成新密钥**（Generate New Key）
6. **复制并保存密钥**（密钥只显示一次，请妥善保存）

### 密钥格式

安全密钥通常是一个长字符串，例如：
```
sk-1234567890abcdef1234567890abcdef12345678
```

---

## 步骤 3: 配置本地 AgentOS

### 3.1 编辑配置文件

打开对应环境的配置文件（开发环境使用 `config/dev.toml`）：

```toml
[agentos]
# AgentOS Control Plane 配置
os_security_key = "sk-your-security-key-here"  # 从 Control Plane 获取的安全密钥（必需）
run_mode = "standalone"  # standalone: 独立运行在 7777 端口（官方推荐）| mounted: 挂载在主应用的 /agentos 路径
os_port = 7777  # AgentOS 独立运行时的端口（官方默认 7777，仅在 standalone 模式下使用）
os_host = "127.0.0.1"  # AgentOS 独立运行时的主机地址（仅在 standalone 模式下使用）
os_name = "Development OS"  # OS 名称，显示在 Control Plane 中
os_tags = ["development", "local"]  # 标签列表，用于组织和过滤
```

**注意**: 
- `os_security_key` 是必需的，用于 Control Plane 认证
- `run_mode = "standalone"` 是官方推荐方式，AgentOS 独立运行在 7777 端口
- `run_mode = "mounted"` 将 AgentOS 挂载在主应用的 `/agentos` 路径下

### 3.2 配置说明

- **`os_security_key`**: 从 Control Plane 获取的安全密钥（必需）。此密钥会设置到环境变量 `OS_SECURITY_KEY` 中，用于 Control Plane 的 Bearer Token 认证
- **`os_port`**: AgentOS 独立运行时的端口（默认 7777）。**注意**: 如果 AgentOS 挂载在主应用的子路径下（如当前实现），此配置不会被使用，将使用主应用的端口
- **`os_name`**: OS 名称，将显示在 Control Plane 的 OS 列表中
- **`os_tags`**: 标签列表，用于在 Control Plane 中组织和过滤多个 OS 实例

### 3.3 环境配置示例

**开发环境** (`config/dev.toml`) - 独立运行模式（推荐）:
```toml
[agentos]
os_security_key = "sk-dev-key-here"  # 从 Control Plane 获取
run_mode = "standalone"  # 独立运行在 7777 端口（官方推荐）
os_port = 7777  # 官方默认端口
os_host = "127.0.0.1"  # 开发环境使用 localhost
os_name = "Development OS"
os_tags = ["development", "local"]
```

**生产环境** (`config/prod.toml`) - 独立运行模式（推荐）:
```toml
[agentos]
os_security_key = "sk-prod-key-here"  # 从 Control Plane 获取
run_mode = "standalone"  # 独立运行在 7777 端口（官方推荐）
os_port = 7777  # 官方默认端口
os_host = "0.0.0.0"  # 生产环境使用 0.0.0.0 以允许外部访问
os_name = "Production OS"
os_tags = ["production", "live"]
```

**挂载模式示例**（使用 base_app 整合，官方推荐）:
```toml
[agentos]
os_security_key = "sk-key-here"
run_mode = "mounted"  # 通过 base_app 整合到主应用
os_name = "Mounted OS"
os_tags = ["mounted"]
```

**重要提示**: 
- **独立运行模式（推荐）**: 端点 URL 为 `http://localhost:7777`（官方标准方式）
- **挂载模式（base_app 整合）**: 端点 URL 为 `http://localhost:8000`（AgentOS 路由直接添加到主应用，无需子路径）
- 使用 `base_app` 方式整合是官方推荐的方式，AgentOS 会将路由和中间件直接添加到现有 FastAPI 应用中

---

## 步骤 4: 启动应用

### 4.1 选择运行模式

根据配置文件中的 `run_mode` 设置，有两种启动方式：

**方式 1: 独立运行（官方推荐，默认）**
- `run_mode = "standalone"`
- AgentOS 运行在独立端口（默认 7777）
- 主应用和 AgentOS 分别运行

**方式 2: 挂载模式**
- `run_mode = "mounted"`
- AgentOS 挂载在主应用的 `/agentos` 路径下
- 主应用和 AgentOS 运行在同一端口

### 4.2 启动独立运行的 AgentOS（推荐）

如果配置为 `run_mode = "standalone"`：

```bash
# 激活虚拟环境（如果使用）
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 方式 1: 使用模块方式启动（推荐）
python -m agno_project.agentos.serve

# 方式 2: 直接运行脚本（如果方式 1 失败）
python src/agno_project/agentos/serve.py
```

AgentOS 将在 `http://localhost:7777` 启动（或配置的端口）。

**启动成功标志**:
- 看到 "OS running on: http://localhost:7777" 消息
- 看到 "🔒 Security Key Enabled"（如果配置了安全密钥）
- 看到 Control Plane 连接信息

### 4.3 启动主应用（如果需要）

主应用可以独立运行，不影响 AgentOS：

```bash
# 启动主应用（RAG 系统）
python -m agno_project.api.run
```

主应用将在 `http://localhost:8000` 启动。

### 4.4 启动挂载模式

如果配置为 `run_mode = "mounted"`：

```bash
# 启动主应用（AgentOS 会自动挂载）
python -m agno_project.api.run
```

AgentOS 将在 `http://localhost:8000/agentos` 可用。

### 4.2 验证 AgentOS 运行状态

应用启动后，检查日志输出：

```
✓ AgentOS 初始化成功
  OS ID: development-os
  OS 名称: Development OS
  Control Plane 安全密钥: 已配置
✓ AgentOS 已集成到主应用，路由挂载在 /agentos
```

### 4.3 检查端点可访问性

根据运行模式检查端点：

**独立运行模式**:
```bash
# 检查 AgentOS 健康状态
curl http://localhost:7777/health

# 检查 AgentOS 状态 API（通过主应用）
curl http://localhost:8000/api/v1/agentos/status
```

**挂载模式（base_app 整合）**:
```bash
# 检查 AgentOS 健康状态（路由直接添加到主应用，无需子路径）
curl http://localhost:8000/health

# 检查 AgentOS 状态 API
curl http://localhost:8000/api/v1/agentos/status
```

**验证步骤**:
1. 健康检查端点应返回 JSON 响应（不是 404）
2. 状态 API 应返回完整的配置和诊断信息
3. 检查 `control_plane_ready` 字段，应该为 `true`（如果配置了安全密钥）

状态 API 应返回：

```json
{
  "status": "running",
  "os_id": "development-os",
  "os_name": "Development OS",
  "os_tags": ["development", "local"],
  "endpoint_url": "http://localhost:8000/agentos",
  "agents_count": 1,
  "agents": [
    {
      "name": "Assistant",
      "id": "assistant",
      "description": "AI Assistant with Knowledge Base"
    }
  ],
  "security_configured": true,
  "control_plane_ready": true
}
```

---

## 步骤 5: 在 Control Plane 中连接

### 5.1 打开连接对话框

1. 在 Control Plane 中，点击顶部导航栏的组织/团队下拉菜单
2. 点击 **"+"**（加号）按钮，位于 "Add new OS" 旁边
3. "Connect your AgentOS" 对话框将打开

### 5.2 选择环境

选择 **"Local"**（本地）或 **"Live"**（生产）：

- **Local**: 连接到运行在本地机器的 AgentOS（开发环境）
- **Live**: 连接到生产环境的 AgentOS（需要 PRO 订阅）

### 5.3 配置连接设置

#### Endpoint URL

根据配置文件中的 `run_mode` 选择正确的端点 URL：

**方式 1: AgentOS 独立运行（官方推荐，默认）**
- **默认本地**: `http://localhost:7777`（AgentOS 官方默认端口）
- **自定义端口**: 如果配置了不同的端口，使用该端口，例如 `http://localhost:8888`
- **生产环境**: 输入生产 HTTPS URL，例如 `https://agentos.your-domain.com` 或 `https://your-domain.com:7777`

**方式 2: AgentOS 通过 base_app 整合到主应用（官方推荐）**
- **默认本地**: `http://localhost:8000`（AgentOS 路由直接添加到主应用，无需子路径）
- **自定义端口**: 如果主应用运行在不同端口，修改端口号，例如 `http://localhost:9000`
- **生产环境**: 输入生产 HTTPS URL，例如 `https://your-domain.com`

**重要**: 
- 确保 AgentOS 实际运行在指定的端点上
- **独立运行模式（推荐）**: 端点 URL 直接使用根路径，例如 `http://localhost:7777`
- **挂载模式（base_app 整合）**: 端点 URL 使用主应用端口，AgentOS 路由直接添加到根路径，例如 `http://localhost:8000`（无需 `/agentos` 子路径）
- 官方推荐使用独立运行模式，端口 7777
- 如果使用挂载模式，推荐使用 `base_app` 方式整合（官方推荐），而不是 `mount` 方式

#### OS Name

为您的 AgentOS 提供一个描述性名称：
- 使用清晰、描述性的名称，如 "Development OS" 或 "Production Chat Bot"
- 此名称将显示在 OS 列表中，帮助您识别不同的实例

#### Tags（可选）

添加标签以组织您的 AgentOS 实例：
- 示例: `development`, `production`, `chatbot`, `research`
- 标签帮助过滤和组织多个 OS 实例
- 点击 **"+"** 按钮添加多个标签

### 5.4 测试和连接

1. 点击 **"CONNECT"** 按钮
2. Control Plane 将尝试建立与您的 AgentOS 的连接
3. 如果成功，您将在组织仪表板中看到新的 OS

---

## 步骤 6: 验证连接

连接成功后，您应该看到：

1. **OS 状态**: 平台中显示 "Running" 指示器
2. **可用功能**: Chat、Knowledge、Memory、Sessions 等应该可以访问
3. **Agent 列表**: 您配置的 Agent 应该出现在聊天界面中

### 验证步骤

1. **检查 OS 状态**
   - 在 Control Plane 的 OS 列表中，确认状态为 "Running"
   - 如果状态为 "Offline" 或 "Error"，检查日志和网络连接

2. **测试 Agent 交互**
   - 打开 Chat 界面
   - 选择您的 Agent
   - 发送测试消息，验证响应

3. **检查知识库**
   - 打开 Knowledge 界面
   - 验证知识库文档是否可见
   - 测试搜索功能

---

## 使用管理界面

### Chat 界面

- **与 Agent 对话**: 选择 Agent 并开始对话
- **会话管理**: 查看和管理所有会话历史
- **消息历史**: 查看完整的对话记录

### Knowledge 界面

- **文档管理**: 上传、编辑和删除知识库文档
- **搜索功能**: 在知识库中搜索内容
- **文档预览**: 查看文档内容和元数据

### Sessions 界面

- **会话列表**: 查看所有会话
- **会话详情**: 查看特定会话的详细信息
- **会话统计**: 查看会话使用统计

### Memory 界面

- **记忆查看**: 查看 Agent 存储的记忆
- **记忆管理**: 编辑和删除记忆条目

### 系统监控

- **性能指标**: 查看系统性能和使用统计
- **运行状态**: 监控 AgentOS 运行状态
- **错误日志**: 查看错误和警告日志

---

## 故障排除

### 问题 1: AgentOS not active / 无法连接到 AgentOS

**症状**: Control Plane 显示 "AgentOS not active"、"Connection Failed" 或 "Offline"

**解决方案**:

1. **确认 AgentOS 正在运行**
   ```bash
   # Windows
   netstat -an | findstr 7777
   
   # Linux/macOS
   lsof -i :7777
   # 或
   netstat -tuln | grep 7777
   ```
   如果端口未被监听，说明 AgentOS 未启动。

2. **检查 AgentOS 启动日志**
   - 启动 AgentOS: `python -m agno_project.agentos.serve`
   - 查看是否有错误信息
   - 确认看到 "OS running on: http://localhost:7777" 消息

3. **验证端点 URL**
   - **独立运行模式**: `http://localhost:7777`（不需要子路径）
   - **挂载模式（base_app 整合）**: `http://localhost:8000`（AgentOS 路由直接添加到主应用，无需子路径）
   - 在浏览器中访问端点，应该能看到响应

4. **检查健康检查端点**
   ```bash
   # 独立运行模式
   curl http://localhost:7777/health
   
   # 挂载模式（base_app 整合）
   curl http://localhost:8000/health
   ```
   应该返回 JSON 响应，而不是 404 或连接错误。

5. **检查状态 API**
   ```bash
   curl http://localhost:8000/api/v1/agentos/status
   ```
   查看返回的诊断信息，确认：
   - `status`: "running"
   - `security_configured`: true
   - `control_plane_ready`: true
   - `endpoint_url`: 正确的端点 URL

6. **检查防火墙设置**
   - 确保端口 7777（独立模式）或 8000（挂载模式）未被阻止
   - 如果使用云服务器，检查安全组规则

7. **查看应用日志**
   - 检查启动日志中的错误信息
   - 确认安全密钥已正确配置

### 问题 2: 安全密钥验证失败

**症状**: 连接时提示 "Authentication Failed" 或 "Invalid token"

**解决方案**:

1. **确认安全密钥已正确配置**
   - 检查配置文件中的 `os_security_key` 是否已填写
   - 确认密钥没有多余的空格或换行符
   - 密钥应该以 `sk-` 开头

2. **检查配置是否正确加载**
   ```bash
   # 访问状态 API 查看配置
   curl http://localhost:8000/api/v1/agentos/status
   ```
   检查返回的 `security_configured` 和 `diagnostics` 字段。

3. **验证环境变量**
   ```bash
   # Windows PowerShell
   $env:OS_SECURITY_KEY
   
   # Linux/macOS
   echo $OS_SECURITY_KEY
   ```
   虽然安全密钥主要通过 `AgnoAPISettings` 传递，但环境变量也会被检查。

4. **重新生成安全密钥**
   - 在 Control Plane 中生成新的安全密钥
   - 更新配置文件
   - 重启 AgentOS

5. **检查 AgentOS 启动日志**
   - 启动时应该看到 "✓ AgentOS 安全密钥已配置（通过 settings 和环境变量）"
   - 如果使用 `agent_os.serve()`，应该看到 "🔒 Security Key Enabled" 消息

### 问题 3: CORS 错误

**症状**: 浏览器控制台显示 CORS 相关错误

**解决方案**:
1. 确认 CORS 中间件已正确配置
2. 检查 `allow_origins` 列表是否包含 Control Plane 域名
3. 开发环境可以临时允许所有来源（`["*"]`）

### 问题 4: Agent 列表为空

**症状**: Control Plane 中看不到 Agent

**解决方案**:
1. 检查 AgentOS 初始化日志，确认 Agent 已创建
2. 访问 `/api/v1/agentos/status` 端点，查看 Agent 列表
3. 确认 Agent 已正确添加到 AgentOS 实例

### 问题 5: 端点返回 404

**症状**: 访问 AgentOS 端点返回 404

**解决方案**:

1. **独立运行模式**
   - 确认 AgentOS 正在运行: `python -m agno_project.agentos.serve`
   - 访问 `http://localhost:7777/health` 应该返回响应
   - 如果返回 404，检查 AgentOS 是否正确启动

2. **挂载模式（base_app 整合）**
   - 确认主应用已启动
   - 检查日志中是否有 "✓ AgentOS 已通过 base_app 方式整合到主应用（官方推荐）"
   - 访问 `http://localhost:8000/health` 应该返回响应（AgentOS 路由直接添加到主应用，无需子路径）
   - 如果返回 404，检查 `run_mode` 配置是否为 "mounted"

3. **验证路由挂载**
   ```bash
   # 检查主应用路由
   curl http://localhost:8000/docs
   # 应该能看到 API 文档，包括 /agentos 路径下的路由
   ```

### 问题 6: AgentOS 启动失败

**症状**: 运行 `python -m agno_project.agentos.serve` 时出错

**解决方案**:

1. **检查配置**
   - 确认 `[agentos]` 配置节存在
   - 确认 `run_mode = "standalone"`
   - 确认 `os_port` 和 `os_host` 配置正确

2. **检查端口占用**
   ```bash
   # Windows
   netstat -ano | findstr :7777
   
   # Linux/macOS
   lsof -i :7777
   ```
   如果端口被占用，修改 `os_port` 或停止占用端口的进程。

3. **检查依赖**
   - 确认所有依赖已安装: `pip install -r requirements.txt`
   - 确认数据库连接正常（MySQL、Milvus）

4. **查看详细错误**
   - 检查启动日志中的完整错误信息
   - 确认 AgentOS 初始化是否成功

---

## 安全建议

### 生产环境

1. **使用 HTTPS**: 生产环境必须使用 HTTPS
2. **安全密钥管理**: 
   - 不要将安全密钥提交到版本控制系统
   - 使用环境变量或密钥管理服务
   - 定期轮换安全密钥
3. **网络隔离**: 限制 AgentOS 端点的网络访问
4. **访问控制**: 使用防火墙和访问控制列表

### 开发环境

1. **本地访问**: 开发环境可以使用 HTTP 和 localhost
2. **密钥保护**: 即使开发环境也要保护安全密钥
3. **测试隔离**: 使用不同的密钥和标签区分测试和生产实例

---

## 高级配置

### 独立运行模式（官方推荐，默认）

AgentOS 默认配置为独立运行模式，这是官方推荐的方式：

1. **配置**: 在配置文件中设置 `run_mode = "standalone"`
2. **启动**: 使用 `python -m agno_project.agentos.serve` 启动 AgentOS
3. **端口**: AgentOS 运行在官方默认端口 7777
4. **在 Control Plane 中连接**: 使用独立端口 URL: `http://localhost:7777`

**优势**:
- 符合官方推荐方式
- 独立端口，便于管理和监控
- Control Plane 可以直接连接到标准端口
- 与主应用解耦，互不影响

### 挂载模式（base_app 整合，官方推荐）

如果需要将 AgentOS 整合到主应用中（使用 `base_app` 方式，官方推荐）：

1. **配置**: 在配置文件中设置 `run_mode = "mounted"`
2. **启动**: 使用 `python -m agno_project.api.run` 启动主应用（AgentOS 会自动通过 `base_app` 整合）
3. **端口**: 使用主应用端口（默认 8000）
4. **在 Control Plane 中连接**: 使用主应用 URL: `http://localhost:8000`（AgentOS 路由直接添加到主应用，无需子路径）

**优势**:
- 统一管理，所有服务在一个端口上
- AgentOS 路由直接添加到主应用，无需子路径
- 使用官方推荐的 `base_app` 方式整合，更符合最佳实践
- 适合需要统一入口的场景

### 多环境管理

使用标签管理多个环境：

```toml
# 开发环境
[agentos]
os_name = "Dev OS"
os_tags = ["dev", "local"]

# 预演环境
[agentos]
os_name = "Staging OS"
os_tags = ["staging", "preview"]

# 生产环境
[agentos]
os_name = "Prod OS"
os_tags = ["prod", "live"]
```

在 Control Plane 中可以使用标签过滤不同的 OS 实例。

---

## 参考资源

- [Agno Control Plane 连接文档](https://docs.agno.com/agent-os/connecting-your-os)
- [AgentOS 安全配置文档](https://docs.agno.com/agent-os/security-authorization)
- [AgentOS API 文档](https://docs.agno.com/agent-os/agent-os-api)
- [AgentOS 配置文档](https://docs.agno.com/agent-os/configuration)
- [Agno 官方文档](https://docs.agno.com)

---

## 快速检查清单

在连接前，请确认：

- [ ] 已在 Control Plane 创建账户和组织
- [ ] 已获取安全密钥
- [ ] 已在配置文件中设置 `os_security_key`
- [ ] 配置文件中的 `run_mode` 设置正确（standalone 或 mounted）
- [ ] AgentOS 已启动（独立模式：`python -m agno_project.agentos.serve`）
- [ ] 端口正在监听（独立模式：7777，挂载模式：8000）
- [ ] 健康检查端点可访问（`/health` 或 `/agentos/health`）
- [ ] `/api/v1/agentos/status` 返回正确状态，`control_plane_ready: true`
- [ ] 在 Control Plane 中正确配置了 Endpoint URL（独立模式：`http://localhost:7777`，挂载模式：`http://localhost:8000/agentos`）

## 快速诊断命令

### 检查 AgentOS 是否运行

```bash
# Windows
netstat -an | findstr 7777

# Linux/macOS
lsof -i :7777
```

### 检查配置和状态

```bash
# 获取详细状态信息（包括诊断信息）
curl http://localhost:8000/api/v1/agentos/status | python -m json.tool

# 检查健康状态（独立模式）
curl http://localhost:7777/health

# 检查健康状态（挂载模式）
curl http://localhost:8000/agentos/health
```

### 验证安全密钥配置

```bash
# 检查状态 API 中的安全配置
curl http://localhost:8000/api/v1/agentos/status | python -m json.tool | grep -A 5 "security"
```

应该看到：
- `security_configured: true`
- `control_plane_ready: true`
- `diagnostics.settings_configured: true`

---

## 支持

如果遇到问题：

1. 查看应用日志获取详细错误信息
2. 检查 [Agno 官方文档](https://docs.agno.com)
3. 访问 [Agno GitHub](https://github.com/agno-ai/agno) 提交问题
4. 联系 Agno 支持团队

---

**最后更新**: 2024年12月

