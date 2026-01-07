# Agno 表创建时机和数据库选择分析

## 问题描述

即使指定了自定义数据库，`agno_sessions` 表以及其他表仍然创建在 `ai` 数据库下。

## 核心概念区分

### 1. MySQL 数据库名称（Database Name）
- **位置**：连接字符串中，如 `mysql+pymysql://user:password@host:port/database_name`
- **作用**：指定连接到哪个 MySQL 数据库
- **配置位置**：`MYSQL_DATABASE` 环境变量
- **示例**：`agno_agents`、`my_custom_db`

### 2. 表名前缀（db_schema）
- **位置**：`MySQLDb` 初始化参数 `db_schema`
- **作用**：用于生成表名前缀
- **配置位置**：`AGNO_DB_SCHEMA` 环境变量
- **默认值**：如果不指定，Agno 框架默认使用 `"ai"`
- **示例**：
  - `db_schema="agno_demo"` → 表名：`agno_demo_sessions`、`agno_demo_memories`
  - 不指定 → 表名：`ai_sessions`、`ai_memories`

## 表创建时机

### 1. 首次使用数据库时
Agno 框架使用**延迟初始化（Lazy Initialization）**策略：
- 表结构在**首次使用数据库时**自动创建
- 不是在 `MySQLDb` 实例化时创建
- 不是在 Agent/Team 创建时创建

### 2. 触发表创建的操作
以下操作会触发表创建：
- 首次调用 `agent.run()` 或 `team.run()`
- 首次访问会话数据
- 首次存储记忆数据
- 首次查询运行历史

### 3. 表创建流程
```
1. Agent/Team 调用 run()
   ↓
2. 需要存储会话数据
   ↓
3. 检查表是否存在
   ↓
4. 如果不存在，使用 SQLAlchemy 创建表
   ↓
5. 表创建在连接字符串指定的数据库中
```

## 问题根源分析

### 问题 1: 表创建在 "ai" 数据库下

**可能原因**：

#### 原因 A: 连接字符串中数据库名称是 "ai"
```python
# 错误的配置
db_url = "mysql+pymysql://user:password@host:port/ai"  # ❌ 数据库名称是 "ai"
```

**检查方法**：
```python
# 在 get_agno_db() 函数中已经有验证逻辑
from sqlalchemy import create_engine, text
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT DATABASE()"))
    actual_db = result.scalar()
    print(f"实际连接的数据库: {actual_db}")
```

#### 原因 B: 连接字符串中没有指定数据库
```python
# 错误的配置
db_url = "mysql+pymysql://user:password@host:port"  # ❌ 没有指定数据库
```

如果连接字符串中没有指定数据库，MySQL 可能会：
- 使用默认数据库（通常是用户默认数据库）
- 或者连接失败

#### 原因 C: db_schema 参数未正确传递
```python
# 错误的配置
db = MySQLDb(db_url=db_url)  # ❌ 没有指定 db_schema，默认使用 "ai"
```

即使数据库名称正确，如果 `db_schema` 未指定，表名会是 `ai_sessions`，但**表仍然应该在连接字符串指定的数据库中创建**。

### 问题 2: 表名是 "ai_sessions" 而不是自定义表名

**原因**：`db_schema` 参数未设置或未正确传递

**解决方案**：
```python
# 正确的配置
db = MySQLDb(
    db_url="mysql+pymysql://user:password@host:port/my_database",
    db_schema="agno_demo"  # ✅ 指定表名前缀
)
# 结果：在 my_database 数据库中创建 agno_demo_sessions 表
```

## 代码检查清单

### 1. 检查环境变量配置

```bash
# 检查 .env 文件
cat .env | grep -E "MYSQL_DATABASE|AGNO_DB_SCHEMA"
```

**应该看到**：
```
MYSQL_DATABASE=agno_agents          # 数据库名称
AGNO_DB_SCHEMA=agno_demo            # 表名前缀（可选）
```

### 2. 检查连接字符串

在 `src/database/agno_mysql_db.py` 的 `get_mysql_db_url()` 函数中：

```python
database = config.get('database', 'agno_agents')  # 检查这里
db_url = f"mysql+pymysql://{user}{password_part}{host}:{port}/{database}"
```

**验证**：确保 `database` 变量不是 `"ai"`

### 3. 检查 MySQLDb 初始化参数

在 `src/database/agno_mysql_db.py` 的 `get_agno_db()` 函数中：

```python
db_kwargs = {"db_url": db_url}

if db_schema:  # ✅ 确保这里正确传递了 db_schema
    db_kwargs['db_schema'] = db_schema

db = MySQLDb(**db_kwargs)
```

### 4. 验证实际连接的数据库

代码中已经有验证逻辑（第 288-302 行）：

```python
from sqlalchemy import create_engine, text
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT DATABASE()"))
    actual_db = result.scalar()
    if actual_db != database_name:
        logger.error(f"❌ 错误: 实际连接的数据库是 '{actual_db}'，而不是配置的 '{database_name}'！")
```

## 解决方案

### 方案 1: 确保环境变量正确配置

```bash
# .env 文件
MYSQL_DATABASE=agno_agents          # 数据库名称（不是 "ai"）
AGNO_DB_SCHEMA=agno_demo            # 表名前缀（可选，但推荐设置）
```

### 方案 2: 检查并修复连接字符串

确保 `get_mysql_db_url()` 返回的连接字符串包含正确的数据库名称：

```python
# 应该返回类似：
# mysql+pymysql://user:password@host:port/agno_agents
# 而不是：
# mysql+pymysql://user:password@host:port/ai
```

### 方案 3: 确保 db_schema 参数传递

在 `get_agno_db()` 函数中，确保 `db_schema` 参数正确传递：

```python
agent_db_config = get_agent_db_config()
db_schema = agent_db_config.get('db_schema')

if db_schema:
    db_kwargs['db_schema'] = db_schema  # ✅ 确保这行代码执行
```

### 方案 4: 重置数据库实例缓存

如果修改了配置，需要重置缓存：

```python
from src.database.agno_mysql_db import reset_db_instance
reset_db_instance()  # 清除缓存，重新加载配置
```

## 调试步骤

### 步骤 1: 检查日志输出

运行程序时，查看日志输出：

```
[数据库配置] 数据库: agno_agents          # ✅ 应该是你的数据库名称
[数据库配置] Schema: agno_demo             # ✅ 如果设置了 AGNO_DB_SCHEMA
✓ 验证成功: 实际连接的数据库是 'agno_agents'  # ✅ 验证通过
```

### 步骤 2: 直接查询数据库

```sql
-- 连接到 MySQL
mysql -u root -p

-- 查看所有数据库
SHOW DATABASES;

-- 查看指定数据库中的表
USE agno_agents;  -- 或你的数据库名称
SHOW TABLES;

-- 如果表在错误的数据库中，检查：
USE ai;  -- 检查是否在 ai 数据库中
SHOW TABLES;
```

### 步骤 3: 检查表名

```sql
-- 查看表名是否符合预期
-- 如果设置了 AGNO_DB_SCHEMA=agno_demo，应该看到：
-- agno_demo_sessions
-- agno_demo_memories
-- agno_demo_runs

-- 如果没有设置，默认是：
-- ai_sessions
-- ai_memories
-- ai_runs
```

## 常见错误示例

### 错误示例 1: 数据库名称和表名前缀混淆

```python
# ❌ 错误：将表名前缀当作数据库名称
MYSQL_DATABASE=ai  # 错误！这应该是数据库名称，不是表名前缀

# ✅ 正确：
MYSQL_DATABASE=agno_agents      # 数据库名称
AGNO_DB_SCHEMA=agno_demo         # 表名前缀
```

### 错误示例 2: 未设置 db_schema

```python
# ❌ 错误：没有传递 db_schema
db = MySQLDb(db_url=db_url)
# 结果：表名是 ai_sessions（在正确的数据库中，但表名不对）

# ✅ 正确：
db = MySQLDb(db_url=db_url, db_schema="agno_demo")
# 结果：表名是 agno_demo_sessions（在正确的数据库中）
```

### 错误示例 3: 连接字符串错误

```python
# ❌ 错误：连接字符串中没有数据库名称
db_url = "mysql+pymysql://user:password@host:port"

# ✅ 正确：
db_url = "mysql+pymysql://user:password@host:port/agno_agents"
```

## 总结

1. **表创建时机**：首次使用数据库时（延迟初始化）
2. **数据库选择**：由连接字符串中的数据库名称决定
3. **表名生成**：由 `db_schema` 参数决定（默认 "ai"）
4. **关键检查点**：
   - 连接字符串中的数据库名称
   - `db_schema` 参数是否正确传递
   - 环境变量是否正确配置

如果表仍然创建在 "ai" 数据库中，最可能的原因是：
- 连接字符串中的数据库名称是 "ai"
- 或者连接字符串中没有指定数据库，MySQL 使用了默认数据库

