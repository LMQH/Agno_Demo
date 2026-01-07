# Agno MySQL 数据库配置详细说明

本文档详细说明了 Agno 框架中 MySQL 数据库的配置方法，包括连接方式、数据库名称配置以及表名自定义方法。

## 目录

- [概述](#概述)
- [MySQL 数据库连接](#mysql-数据库连接)
- [配置方式](#配置方式)
- [自定义数据库名称](#自定义数据库名称)
- [自定义表名](#自定义表名)
- [使用示例](#使用示例)
- [数据库初始化](#数据库初始化)
- [注意事项](#注意事项)
- [常见问题](#常见问题)

---

## 概述

Agno 框架使用 `agno.db.mysql.MySQLDb` 类来连接 MySQL 数据库，用于存储 Agent 的会话数据、运行历史、记忆等信息。

### 核心特性

- ✅ 支持 MySQL 5.7+ 数据库
- ✅ 支持自定义数据库名称
- ✅ 支持自定义表名（通过 `session_table`、`memory_table` 等参数）
- ✅ 基于 SQLAlchemy 实现
- ✅ 支持 UTF-8 编码（utf8mb4）
- ✅ 自动创建表结构

---

## MySQL 数据库连接

### 基本导入

```python
from agno.db.mysql import MySQLDb
```

### 初始化方式

Agno 的 `MySQLDb` 类支持以下初始化参数：

#### 连接参数（二选一，必需）

- **`db_url`** (str, optional): MySQL 数据库连接字符串。采用 SQLAlchemy 格式。
- **`db_engine`** (Engine, optional): SQLAlchemy Engine 对象。如果提供了 `db_engine`，则不需要 `db_url`。

**连接优先级**：
1. 如果提供了 `db_engine`，优先使用 `db_engine`
2. 如果未提供 `db_engine` 但提供了 `db_url`，使用 `db_url` 创建 Engine
3. 如果两者都未提供，抛出 `ValueError`

#### 可选参数

- **`id`** (str, optional): 数据库实例的唯一标识符。如果不指定，会根据 `db_url` 或 `db_engine.url` 和 `db_schema` 自动生成。
- **`db_schema`** (str, optional): 数据库名称（在 MySQL 中，schema 与 database 是同义词）。**推荐方式**：在 `db_url` 中不包含数据库名，通过 `db_schema` 参数指定数据库名。如果不指定，默认使用 `"ai"`。
- **`create_schema`** (bool, optional): 是否自动创建数据库 schema（如果不存在）。如果设置为 `False`，schema 需要通过外部方式管理（如迁移工具）。默认值为 `True`。
- **`session_table`** (str, optional): 会话表名称。如果不指定，默认使用 `"agno_sessions"`。
- **`memory_table`** (str, optional): 记忆表名称。如果不指定，默认使用 `"agno_memories"`。
- **`traces_table`** (str, optional): 追踪表名称。如果不指定，默认使用 `"agno_traces"`。
- **`spans_table`** (str, optional): Span 表名称。如果不指定，默认使用 `"agno_spans"`。
- **`metrics_table`** (str, optional): 指标表名称。如果不指定，默认使用 `"agno_metrics"`。
- **`eval_table`** (str, optional): 评估表名称。如果不指定，默认使用 `"agno_eval_runs"`。
- **`knowledge_table`** (str, optional): 知识表名称。如果不指定，默认使用 `"agno_knowledge"`。
- **`culture_table`** (str, optional): 文化知识表名称。如果不指定，默认使用 `"agno_culture"`。
- **`versions_table`** (str, optional): 版本表名称。如果不指定，默认使用 `"agno_schema_versions"`。

### 基本连接示例

```python
from agno.db.mysql import MySQLDb
from sqlalchemy import create_engine

# 方式 1: 推荐方式 - db_url 不包含数据库名，通过 db_schema 指定数据库名
db = MySQLDb(
    db_url="mysql+pymysql://user:password@localhost:3306",  # 数据库连接（不包含数据库名）
    db_schema="agno_memory"  # 数据库名
)

# 方式 2: 使用 db_url 包含数据库名（兼容方式）
db = MySQLDb(db_url="mysql+pymysql://user:password@host:port/database")

# 方式 3: 使用 db_engine（适用于需要自定义 Engine 配置的场景）
engine = create_engine("mysql+pymysql://user:password@host:port/database")
db = MySQLDb(db_engine=engine)

# 方式 4: 推荐方式 + 自定义表名
db = MySQLDb(
    db_url="mysql+pymysql://user:password@localhost:3306",  # 数据库连接
    db_schema="agno_memory",  # 数据库名
    session_table="custom_sessions",  # 自定义表名
    memory_table="custom_memories"
)

# 方式 5: 禁用自动创建 schema
db = MySQLDb(
    db_url="mysql+pymysql://user:password@localhost:3306",
    db_schema="agno_memory",
    create_schema=False
)
```

---

## 配置方式

项目支持通过 TOML 配置文件来管理 MySQL 连接配置。

### 配置文件结构

在 `config/` 目录下的 TOML 配置文件中（如 `dev.toml`、`prod.toml` 等）：

```toml
[database.mysql]
host = "localhost"
port = 3306
user = "root"
password = "your_password"
database = "agno_demo"  # MySQL 数据库名称
charset = "utf8mb4"
pool_size = 5

[agent_db]
enabled = true
num_history_runs = 5
db_schema = "ai"  # SQLAlchemy schema 名称（在 MySQL 中与 database 同义，默认 "ai"）
session_table = "agno_sessions"  # 可选：自定义会话表名（默认 "agno_sessions"）
memory_table = "agno_memories"  # 可选：自定义记忆表名（默认 "agno_memories"）
```

### 配置说明

#### `[database.mysql]` 部分

| 字段 | 类型 | 说明 | 必需 |
|------|------|------|------|
| `host` | str | MySQL 服务器地址 | 是 |
| `port` | int | MySQL 服务器端口 | 否（默认 3306） |
| `user` | str | MySQL 用户名 | 是 |
| `password` | str | MySQL 密码 | 是 |
| `database` | str | **MySQL 数据库名称** | 是 |
| `charset` | str | 字符集编码 | 否（默认 utf8mb4） |
| `pool_size` | int | 连接池大小 | 否（默认 5） |

#### `[agent_db]` 部分

| 字段 | 类型 | 说明 | 必需 |
|------|------|------|------|
| `enabled` | bool | 是否启用 Agent 数据库 | 否（默认 true） |
| `num_history_runs` | int | 历史记录运行次数 | 否（默认 5） |
| `db_schema` | str | SQLAlchemy schema 名称（在 MySQL 中与 database 同义），默认 `"ai"` | 否 |
| `session_table` | str | 自定义会话表名，默认 `"agno_sessions"` | 否 |
| `memory_table` | str | 自定义记忆表名，默认 `"agno_memories"` | 否 |

---

## 自定义数据库名称

### 数据库名称 vs Schema vs 表名

需要区分三个概念：

1. **MySQL 数据库名称** (`database.mysql.database`)：
   - 这是 MySQL 数据库中实际的数据库（database）名称
   - 在连接字符串中指定：`mysql+pymysql://user:password@host:port/database_name`
   - 示例：`agno_demo`、`agno_rag_prod` 等

2. **SQLAlchemy Schema** (`db_schema` 参数)：
   - 在 MySQL 中，schema 与 database 是同义词
   - 用于 SQLAlchemy 的 schema 设置，指定表所属的 schema
   - 如果不指定，默认使用 `"ai"`
   - **注意**：`db_schema` 不会影响表名的生成

3. **表名** (`session_table`、`memory_table` 等参数)：
   - 直接指定表名，不通过 `db_schema` 生成
   - 默认表名：`agno_sessions`、`agno_memories`、`agno_traces` 等
   - 可以通过参数完全自定义

### 在配置文件中设置

```toml
[database.mysql]
database = "my_custom_database"  # MySQL 数据库名称

[agent_db]
db_schema = "ai"                  # SQLAlchemy schema（默认 "ai"）
session_table = "my_sessions"     # 自定义表名
memory_table = "my_memories"      # 自定义表名
```

### 在代码中使用

```python
from agno.db.mysql import MySQLDb

# MySQL 数据库名称：my_custom_database
# Schema：my_custom_database（通过 db_schema 指定）
# 表名：my_sessions, my_memories（自定义）
db = MySQLDb(
    db_url="mysql+pymysql://user:password@host:port",  # 数据库连接（不包含数据库名）
    db_schema="my_custom_database",  # 数据库名
    session_table="my_sessions",  # 直接指定表名
    memory_table="my_memories"   # 直接指定表名
)
```

---

## 自定义表名

Agno 框架在 MySQL 数据库中会创建以下表来存储数据：

### 默认表名

如果不指定表名参数，Agno 框架使用以下默认表名：

| 表名 | 说明 |
|------|------|
| `agno_sessions` | 会话表 |
| `agno_memories` | 记忆表 |
| `agno_traces` | 追踪表 |
| `agno_spans` | Span 表 |
| `agno_metrics` | 指标表 |
| `agno_eval_runs` | 评估运行表 |
| `agno_knowledge` | 知识表 |
| `agno_culture` | 文化知识表 |
| `agno_schema_versions` | Schema 版本表 |

### 自定义表名

可以通过 `MySQLDb` 初始化参数直接指定表名：

```python
from agno.db.mysql import MySQLDb

db = MySQLDb(
    db_url="mysql+pymysql://user:password@host:port",  # 数据库连接（不包含数据库名）
    db_schema="agno_demo",  # 数据库名
    session_table="custom_sessions",    # 自定义会话表名
    memory_table="custom_memories",     # 自定义记忆表名
    traces_table="custom_traces",       # 自定义追踪表名
    # ... 其他表名参数
)
```

### 在配置文件中设置

```toml
[agent_db]
session_table = "custom_sessions"    # 自定义会话表名
memory_table = "custom_memories"     # 自定义记忆表名
traces_table = "custom_traces"       # 自定义追踪表名
```

**重要说明**：
- 表名通过 `session_table`、`memory_table` 等参数直接指定，**不通过 `db_schema` 生成**
- `db_schema` 参数仅用于 SQLAlchemy 的 schema 设置（在 MySQL 中与 database 同义）
- 每个表名都可以独立自定义，互不影响

### 实现示例

#### 方式 1: 通过配置文件（推荐）

```toml
# config/dev.toml
[database.mysql]
database = "agno_demo"

[agent_db]
db_schema = "ai"  # SQLAlchemy schema（可选，默认 "ai"）
session_table = "agno_sessions"  # 可选，默认 "agno_sessions"
memory_table = "agno_memories"  # 可选，默认 "agno_memories"
```

然后在代码中：

```python
from agno_project.config import get_config
from agno.db.mysql import MySQLDb

config = get_config()
mysql_config = config.mysql
agent_db_config = config.agent_db

# 构建连接字符串
db_url = (
    f"mysql+pymysql://{mysql_config.user}:{mysql_config.password}"
    f"@{mysql_config.host}:{mysql_config.port}/{mysql_config.database}"
)
if mysql_config.charset:
    db_url += f"?charset={mysql_config.charset}"

# 创建数据库连接
db_kwargs = {"db_url": db_url}
if agent_db_config.db_schema:
    db_kwargs["db_schema"] = agent_db_config.db_schema
if agent_db_config.session_table:
    db_kwargs["session_table"] = agent_db_config.session_table
if agent_db_config.memory_table:
    db_kwargs["memory_table"] = agent_db_config.memory_table

db = MySQLDb(**db_kwargs)
```

#### 方式 2: 直接在代码中指定

```python
from agno.db.mysql import MySQLDb

# 推荐方式：使用自定义数据库名称和表名
db = MySQLDb(
    db_url="mysql+pymysql://root:password@localhost:3306",  # 数据库连接（不包含数据库名）
    db_schema="my_database",  # 数据库名
    session_table="my_sessions",  # 自定义表名
    memory_table="my_memories"   # 自定义表名
)
```

---

## 使用示例

### 示例 1: Agent 使用 MySQL 数据库

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.mysql import MySQLDb

# 创建 MySQL 数据库连接（推荐方式）
db = MySQLDb(
    db_url="mysql+pymysql://root:password@localhost:3306",  # 数据库连接
    db_schema="agno_demo"  # 数据库名
)

# 创建 Agent 并使用 MySQL 数据库
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    user_id="user-123",
    add_history_to_context=True,
    num_history_runs=5,
)

response = agent.run("Hello, how are you?")
```

### 示例 2: Team 使用 MySQL 数据库

```python
from agno.team.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.mysql import MySQLDb

# 创建 MySQL 数据库连接（推荐方式）
db = MySQLDb(
    db_url="mysql+pymysql://root:password@localhost:3306",  # 数据库连接
    db_schema="agno_demo"  # 数据库名
)

# 创建成员 Agent
researcher = Agent(
    name="Researcher",
    model=OpenAIChat(id="gpt-4o"),
)

writer = Agent(
    name="Writer",
    model=OpenAIChat(id="gpt-4o"),
)

# 创建 Team 并使用 MySQL 数据库
team = Team(
    members=[researcher, writer],
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    instructions="Research and write articles",
)
```

### 示例 3: Workflow 使用 MySQL 数据库

```python
from agno.workflow.workflow import Workflow
from agno.db.mysql import MySQLDb

# 创建 MySQL 数据库连接（推荐方式）
db = MySQLDb(
    db_url="mysql+pymysql://root:password@localhost:3306",  # 数据库连接
    db_schema="agno_demo"  # 数据库名
)

# 创建 Workflow
workflow = Workflow(
    name="My Workflow",
    steps=my_workflow_steps,
    db=db,
)
```

### 示例 4: 从项目配置读取（推荐）

```python
from agno_project.config import get_config
from agno.db.mysql import MySQLDb

def create_db_connection():
    """从配置文件创建 MySQL 数据库连接"""
    config = get_config()
    mysql_config = config.mysql
    agent_db_config = config.agent_db
    
    # 构建 MySQL 连接字符串（推荐方式：不包含数据库名）
    db_url = (
        f"mysql+pymysql://{mysql_config.user}:{mysql_config.password}"
        f"@{mysql_config.host}:{mysql_config.port}"
    )
    if mysql_config.charset:
        db_url += f"?charset={mysql_config.charset}"
    
    # 创建 MySQL 数据库连接
    db_kwargs = {"db_url": db_url}
    # 使用 db_schema 指定数据库名（推荐方式）
    db_kwargs["db_schema"] = agent_db_config.db_schema or mysql_config.database
    if agent_db_config.session_table:
        db_kwargs["session_table"] = agent_db_config.session_table
    if agent_db_config.memory_table:
        db_kwargs["memory_table"] = agent_db_config.memory_table
    
    return MySQLDb(**db_kwargs)

# 使用
db = create_db_connection()
```

---

## 数据库连接字符串格式

MySQL 数据库连接字符串采用 SQLAlchemy 格式，直接传递给 `create_engine()` 函数。

### 基本格式

**推荐格式**（数据库名通过 `db_schema` 参数指定）：
```
mysql+pymysql://[用户名]:[密码]@[主机]:[端口][?参数名=参数值&参数名=参数值]
```

**兼容格式**（数据库名包含在 URL 中）：
```
mysql+pymysql://[用户名]:[密码]@[主机]:[端口]/[数据库名][?参数名=参数值&参数名=参数值]
```

### 格式说明

- **协议**: `mysql+pymysql://`（使用 PyMySQL 驱动）
- **用户名**: MySQL 用户名
- **密码**: MySQL 密码（如果密码为空，格式为 `mysql+pymysql://user@host:port`）
- **主机**: MySQL 服务器地址
- **端口**: MySQL 服务器端口（默认 3306）
- **数据库名**: 
  - **推荐方式**：不在 URL 中指定，通过 `db_schema` 参数指定
  - **兼容方式**：在 URL 中指定（格式：`/database_name`）
- **查询参数**: 可选的连接参数，使用 `?参数名=参数值&参数名=参数值` 格式

### 常用查询参数

SQLAlchemy 支持以下常用查询参数（通过 URL 查询字符串传递）：

- **`charset`**: 字符集编码（如 `charset=utf8mb4`）
- **`connect_timeout`**: 连接超时时间（秒）
- **`read_timeout`**: 读取超时时间（秒）
- **`write_timeout`**: 写入超时时间（秒）
- **`autocommit`**: 是否自动提交（`True`/`False`）

**注意**：`db_url` 直接传递给 SQLAlchemy 的 `create_engine()`，因此支持所有 SQLAlchemy 支持的连接参数。更多参数请参考 [SQLAlchemy 文档](https://docs.sqlalchemy.org/en/20/core/engines.html#mysql)。

### 示例

```python
# 推荐方式：db_url 不包含数据库名，通过 db_schema 指定
db = MySQLDb(
    db_url="mysql+pymysql://root:password@localhost:3306",  # 数据库连接（不包含数据库名）
    db_schema="agno_memory"  # 数据库名
)

# 推荐方式：带字符集编码
db = MySQLDb(
    db_url="mysql+pymysql://root:password@localhost:3306?charset=utf8mb4",
    db_schema="agno_memory"
)

# 推荐方式：无密码
db = MySQLDb(
    db_url="mysql+pymysql://root@localhost:3306",
    db_schema="agno_memory"
)

# 推荐方式：远程服务器
db = MySQLDb(
    db_url="mysql+pymysql://user:password@192.168.1.100:3306",
    db_schema="agno_prod"
)

# 兼容方式：数据库名包含在 URL 中
db_url = "mysql+pymysql://root:password@localhost:3306/agno_demo"
db = MySQLDb(db_url=db_url)

# 使用 db_engine 方式（可以传递更多 Engine 配置）
from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://root:password@localhost:3306",  # 不包含数据库名
    pool_size=10,
    pool_recycle=3600,
    echo=True  # 打印 SQL 语句
)
db = MySQLDb(
    db_engine=engine,
    db_schema="agno_memory"  # 通过 db_schema 指定数据库名
)
```

---

## 数据库初始化

### 手动创建数据库

在首次使用 MySQL 数据库之前，需要先创建数据库：

```sql
CREATE DATABASE agno_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 自动创建表结构

Agno 框架会在首次连接时自动创建所需的表结构。无需手动创建表。

### 验证连接和表创建

```python
from agno.db.mysql import MySQLDb

try:
    db = MySQLDb(
        db_url="mysql+pymysql://root:password@localhost:3306",  # 数据库连接
        db_schema="agno_demo"  # 数据库名
    )
    print("✓ MySQL 连接成功")
    print("✓ 表结构将在首次使用时自动创建")
except Exception as e:
    print(f"✗ MySQL 连接失败: {e}")
```

### 查看创建的表

连接到 MySQL 数据库并执行：

```sql
USE agno_demo;
SHOW TABLES;
```

预期输出（使用默认表名）：

```
+---------------------------+
| Tables_in_agno_demo       |
+---------------------------+
| agno_sessions             |
| agno_memories             |
| agno_traces               |
| agno_spans                |
| agno_metrics              |
| agno_eval_runs            |
| agno_knowledge            |
| agno_culture              |
| agno_schema_versions      |
+---------------------------+
```

---

## 注意事项

### 1. 依赖安装

使用 MySQL 数据库需要安装以下依赖：

```bash
pip install pymysql sqlalchemy
```

### 2. 字符编码

建议使用 `utf8mb4` 字符集，以支持完整的 Unicode 字符（包括 emoji）：

```sql
CREATE DATABASE agno_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 数据库名称、Schema 和表名的区别

- **数据库名称** (`database.mysql.database`): 指定连接到哪个 MySQL 数据库
- **Schema** (`db_schema`): SQLAlchemy schema 名称，在 MySQL 中与 database 同义，默认 `"ai"`
- **表名** (`session_table`、`memory_table` 等): 直接指定表名，默认 `"agno_sessions"`、`"agno_memories"` 等

**重要**：`db_schema` 不会影响表名的生成。表名通过 `session_table`、`memory_table` 等参数直接指定。

```toml
[database.mysql]
database = "production_db"  # 连接到 production_db 数据库

[agent_db]
db_schema = "ai"            # SQLAlchemy schema（默认 "ai"）
session_table = "my_sessions"  # 直接指定表名
memory_table = "my_memories"   # 直接指定表名
```

### 4. 连接复用

MySQL 数据库连接应该被重用，避免在循环中创建新的连接。建议将数据库实例作为全局变量或通过依赖注入的方式共享。

### 5. 生产环境建议

- ✅ 使用连接池管理数据库连接（已在 `MySQLConfig` 中配置 `pool_size`）
- ✅ 配置适当的超时时间
- ✅ 使用 SSL 加密连接（生产环境）
- ✅ 定期备份数据库
- ✅ 监控数据库性能
- ✅ 使用强密码和权限控制

### 6. 错误处理

始终使用 try-except 来处理数据库连接错误：

```python
from agno.db.mysql import MySQLDb

try:
    db = MySQLDb(
        db_url="mysql+pymysql://user:password@host:port",  # 数据库连接
        db_schema="agno_demo"  # 数据库名
    )
except Exception as e:
    print(f"MySQL 连接失败: {e}")
    # 处理错误...
```

---

## 常见问题

### Q1: 如何验证 MySQL 连接是否成功？

A: 可以尝试创建一个 Agent 并运行一次查询，或直接测试连接：

```python
from agno.db.mysql import MySQLDb

try:
    db = MySQLDb(
        db_url="mysql+pymysql://user:password@host:port",  # 数据库连接
        db_schema="agno_demo"  # 数据库名
    )
    print("✓ MySQL 连接成功")
except Exception as e:
    print(f"✗ MySQL 连接失败: {e}")
```

### Q2: 如何查看实际创建的表名？

A: 连接到 MySQL 数据库并执行：

```sql
USE your_database_name;
SHOW TABLES;
```

### Q3: `db_schema` 参数的作用是什么？

A: `db_schema` 参数用于设置 SQLAlchemy 的 schema。在 MySQL 中，schema 与 database 是同义词。**重要**：`db_schema` 不会影响表名的生成。表名通过 `session_table`、`memory_table` 等参数直接指定。

### Q4: 如何自定义表名？

A: 表名通过 `MySQLDb` 初始化参数直接指定：
- `session_table`: 会话表名（默认 `"agno_sessions"`）
- `memory_table`: 记忆表名（默认 `"agno_memories"`）
- `traces_table`: 追踪表名（默认 `"agno_traces"`）
- 等等...

**注意**：表名不通过 `db_schema` 生成，而是直接指定。

### Q5: 支持哪些 MySQL 版本？

A: 建议使用 MySQL 5.7+ 或 MariaDB 10.2+。

### Q6: 如何迁移到新的数据库名称或表名？

A: 
1. 更新配置文件中的 `database.mysql.database` 和/或表名参数（`session_table`、`memory_table` 等）
2. 如果需要迁移数据，使用 `mysqldump` 导出旧数据，然后导入到新数据库
3. 重启应用，Agno 框架会自动在新位置创建表结构

### Q7: `db_url` 和 `db_engine` 有什么区别？应该使用哪个？

A: 
- **`db_url`**: 字符串格式的连接 URL，由 `MySQLDb` 内部调用 `create_engine(db_url)` 创建 Engine。适合大多数场景，简单直接。
- **`db_engine`**: 预创建的 SQLAlchemy Engine 对象。适合需要自定义 Engine 配置的场景（如连接池大小、超时设置、日志等）。

**推荐**：大多数情况下使用 `db_url` 即可。如果需要精细控制连接池或 Engine 行为，使用 `db_engine`。

```python
# 使用 db_url（推荐方式）
db = MySQLDb(
    db_url="mysql+pymysql://user:password@host:port",  # 数据库连接
    db_schema="agno_demo"  # 数据库名
)

# 使用 db_engine（需要自定义配置时）
from sqlalchemy import create_engine
engine = create_engine(
    "mysql+pymysql://user:password@host:port/database",
    pool_size=20,
    pool_recycle=3600
)
db = MySQLDb(db_engine=engine)
```

### Q8: 连接字符串支持哪些参数？

A: `db_url` 支持所有 SQLAlchemy 支持的连接参数，通过 URL 查询字符串传递。常用参数包括：
- `charset`: 字符集（如 `charset=utf8mb4`）
- `connect_timeout`: 连接超时（秒）
- `read_timeout`: 读取超时（秒）
- `write_timeout`: 写入超时（秒）

更多参数请参考 [SQLAlchemy MySQL 文档](https://docs.sqlalchemy.org/en/20/core/engines.html#mysql)。

---

## 参考

- [Agno 官方文档](https://docs.agno.com)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [PyMySQL 文档](https://pymysql.readthedocs.io/)

---

**最后更新**: 基于 Agno 官方文档和项目实际实现
