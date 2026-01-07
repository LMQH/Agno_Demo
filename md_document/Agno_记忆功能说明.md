# Agno 记忆功能说明

## 概述

Agno 框架提供了强大的用户记忆（Memory）功能，允许智能体记住与用户交互的历史信息，并在后续对话中利用这些记忆提供更加个性化和连贯的响应。记忆系统支持多种数据库后端，可以自动存储和检索用户相关信息。

**记忆 vs 会话历史**：
- **记忆（Memory）**：存储从对话中学到的用户事实和偏好（如姓名、习惯），是长期持久化的信息
- **会话历史（Session History）**：存储对话消息，仅用于维持当前对话连贯性

---

## 记忆类型

Agno 提供两种记忆管理方式：

### 1. 自动记忆（Automatic Memory）
- 通过 `enable_user_memories=True` 启用
- 智能体在每次运行后**自动**创建和更新记忆
- 无需手动干预
- 适用于需要一致记忆行为的场景

### 2. 智能体控制记忆（Agentic Memory）
- 通过 `enable_agentic_memory=True` 启用
- 智能体获得对记忆管理的**完全控制权**
- 智能体通过内置工具自主决定何时创建、更新或删除记忆
- 适用于复杂工作流和多轮交互的场景

> ⚠️ **注意**：`enable_user_memories` 和 `enable_agentic_memory` 互斥，不能同时启用。

---

## Agent 记忆相关参数

### enable_user_memories
- **类型**: `bool`
- **默认值**: `False`
- **说明**: 启用自动用户记忆功能。设置为 `True` 时，智能体会在每次运行后自动从对话中提取重要信息并存储为用户记忆。

### enable_agentic_memory
- **类型**: `bool`
- **默认值**: `False`
- **说明**: 启用智能体控制的记忆功能。启用后，智能体可以通过内置工具自主决定何时创建、更新或删除记忆。

### add_memories_to_context
- **类型**: `bool`
- **默认值**: `True`（当启用记忆时）
- **说明**: 是否将用户记忆添加到对话上下文中。设置为 `True` 时，相关的历史记忆会被自动添加到每次对话的上下文中。

### memory_manager
- **类型**: `MemoryManager | None`
- **默认值**: `None`
- **说明**: 自定义记忆管理器实例。如果不提供，框架会使用默认的 MemoryManager。

### memory_table
- **类型**: `str | None`
- **默认值**: `None`（使用 `agno_memories`）
- **说明**: 自定义记忆表名。

### user_id
- **类型**: `str`
- **必需**: ✅ **是**
- **说明**: 用户唯一标识符，用于区分不同用户的记忆。

### db
- **类型**: `MySQLDb | PostgresDb | SqliteDb | RedisDb | MongoDb`
- **必需**: ✅ **是**（使用记忆功能时）
- **说明**: 数据库实例，用于持久化存储记忆数据。

---

## 记忆数据模型（Memory Data Model）

每条存储的记忆包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `memory_id` | `str` | 记忆的唯一标识符 |
| `memory` | `str` | 记忆内容 |
| `topics` | `List[str]` | 记忆的主题列表（分类标签） |
| `input` | `str` | 生成该记忆的原始输入 |
| `user_id` | `str` | 关联的用户 ID |
| `agent_id` | `str` | 关联的智能体 ID |
| `team_id` | `str` | 关联的团队 ID |
| `created_at` | `int` | 记忆创建时间戳 |
| `updated_at` | `int` | 记忆最后更新时间戳 |

---

## MemoryManager 配置（自定义记忆管理器）

### MemoryManager 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db` | `BaseDb` | **必需** | 用于存储记忆的数据库实例 |
| `model` | `BaseModel` | `None` | 用于记忆创建和更新的模型。可指定更便宜的模型减少成本 |
| `system_message` | `str` | `None` | 记忆管理器的自定义系统提示 |
| `memory_capture_instructions` | `str` | `None` | 用于记忆创建和过滤的自定义指令 |
| `additional_instructions` | `str` | `None` | 添加到系统消息的额外指令 |
| `memory_optimization_strategy` | `MemoryOptimizationStrategyType` | `None` | 记忆优化策略 |
| `num_memories` | `int` | `None` | 返回的记忆数量限制 |

### 示例：自定义 MemoryManager

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.models.openai import OpenAIChat

db = SqliteDb(db_file="agno.db")

# 创建自定义记忆管理器
memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-4o-mini"),  # 使用更便宜的模型
    system_message="自定义系统提示",
    memory_capture_instructions="仅记录用户明确表达的偏好",
    additional_instructions="请确保记忆中不包含敏感信息",
)

agent = Agent(
    db=db,
    user_id="user-123",
    memory_manager=memory_manager,
    enable_user_memories=True,
)
```

---

## 自定义记忆指令（Custom Memory Instructions）

通过 `memory_capture_instructions` 和 `additional_instructions` 参数控制记忆行为：

```python
memory_manager = MemoryManager(
    db=db,
    # 记忆捕获指令 - 控制什么信息应该被记忆
    memory_capture_instructions="""
    Only store the following types of information:
    - User preferences and habits
    - Important dates and events
    - Professional information
    Do NOT store:
    - Sensitive personal data
    - Temporary information
    """,
    # 额外指令 - 添加到系统消息
    additional_instructions="Summarize memories concisely",
)
```

---

## 手动记忆检索（Manual Memory Retrieval）

除了自动检索，还可以手动检索用户的记忆：

```python
# 方法1：通过 Agent 检索
memories = agent.get_user_memories(user_id="user-123")
for memory in memories:
    print(f"Memory: {memory.memory}")
    print(f"Topics: {memory.topics}")
    print(f"Updated: {memory.updated_at}")

# 方法2：直接通过 MemoryManager 检索
from agno.memory import MemoryManager

memory_manager = MemoryManager(db=db)
memories = memory_manager.get_user_memories(user_id="user-123")
```

---

## 记忆搜索（Memory Search）

根据特定条件搜索相关记忆：

```python
from agno.memory import MemoryManager

memory_manager = MemoryManager(db=db)

# 搜索包含特定主题的记忆
memories = memory_manager.search_memories(
    user_id="user-123",
    query="programming preferences",  # 搜索查询
    topics=["hobbies", "work"],       # 按主题过滤
    limit=10,                          # 限制结果数量
)
```

---

## 处理记忆（Working with Memories）

### 记忆创建（Memory Creation）

```python
from agno.memory import MemoryManager

memory_manager = MemoryManager(db=db)

# 手动创建记忆
memory_manager.create_memory(
    user_id="user-123",
    memory="User prefers Python for backend development",
    topics=["programming", "preferences"],
)
```

### 记忆更新

```python
# 更新现有记忆
memory_manager.update_memory(
    memory_id="memory-abc-123",
    memory="User now prefers Go for backend development",
    topics=["programming", "preferences"],
)
```

### 记忆删除

```python
# 删除特定记忆
memory_manager.delete_memory(memory_id="memory-abc-123")

# 清除用户的所有记忆
memory_manager.clear_user_memories(user_id="user-123")
```

---

## 独立记忆管理器（Standalone Memory）

MemoryManager 可以独立于 Agent 使用：

```python
from agno.memory import MemoryManager
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

db = SqliteDb(db_file="memories.db")

# 创建独立的记忆管理器
memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-4o"),
)

# 直接使用记忆管理器
memory_manager.create_memory(
    user_id="user-123",
    memory="User's favorite color is blue",
    topics=["preferences"],
)

# 检索记忆
memories = memory_manager.get_user_memories(user_id="user-123")

# 搜索记忆
results = memory_manager.search_memories(
    user_id="user-123",
    query="color preferences",
)
```

---

## 记忆优化（Memory Optimization）

### 优化策略

Agno 提供记忆优化策略来提升存储和检索效率：

| 策略 | 说明 |
|------|------|
| `SummarizeOldest` | 总结并合并最旧的记忆 |
| `LastN` | 仅保留最近 N 条记忆 |

### 配置优化策略

```python
from agno.memory import MemoryManager, SummarizeOldest

memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-4o"),
    memory_optimization_strategy=SummarizeOldest(
        num_memories=100,  # 当记忆超过100条时触发优化
    ),
)
```

### 手动优化

```python
# 手动触发记忆优化
memory_manager.optimize_memories(user_id="user-123")
```

---

## 使用记忆工具（Using Memory Tools）

启用 `enable_agentic_memory=True` 时，智能体可以使用内置记忆工具：

### 可用工具

| 工具 | 说明 |
|------|------|
| `create_memory` | 创建新记忆 |
| `update_memory` | 更新现有记忆 |
| `delete_memory` | 删除记忆 |
| `search_memories` | 搜索记忆 |
| `get_memories` | 获取所有记忆 |

### 示例

```python
agent = Agent(
    db=db,
    user_id="user-123",
    enable_agentic_memory=True,  # 启用智能体控制记忆
)

# 智能体可以使用工具管理记忆
agent.print_response("Remember that I prefer dark mode in all applications")
# 智能体会调用 create_memory 工具

agent.print_response("What are my preferences?")
# 智能体会调用 search_memories 或 get_memories 工具
```

---

## 智能体之间共享记忆（Sharing Memory Between Agents）

多个智能体可以通过共享同一数据库和 `user_id` 来共享记忆：

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="shared_memories.db")
user_id = "user-123"

# 智能体1 创建记忆
agent1 = Agent(
    name="Agent1",
    db=db,
    user_id=user_id,
    enable_user_memories=True,
)
agent1.print_response("I like Italian food")

# 智能体2 可以访问相同的记忆
agent2 = Agent(
    name="Agent2",
    db=db,
    user_id=user_id,
    enable_user_memories=True,
)
agent2.print_response("What food do I like?")
# Agent2 能够访问 Agent1 创建的记忆
```

---

## Teams with Memory（团队记忆）

### Team 记忆相关参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_team_history` | `bool` | `True` | 启用团队运行历史 |
| `num_history_runs` | `int` | `3` | 添加到上下文的历史运行数量 |
| `share_member_memories` | `bool` | `False` | 成员智能体之间共享记忆 |
| `enable_agentic_memory` | `bool` | `False` | 启用团队级别的智能体控制记忆 |
| `memory_manager` | `MemoryManager` | `None` | 团队的自定义记忆管理器 |

### 示例：团队共享记忆

```python
from agno.team.team import Team
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="team.db")

agent1 = Agent(name="Researcher", db=db)
agent2 = Agent(name="Writer", db=db)

team = Team(
    name="ContentTeam",
    members=[agent1, agent2],
    db=db,
    user_id="user-123",
    share_member_memories=True,  # 成员之间共享记忆
    enable_team_history=True,    # 启用团队历史
)
```

---

## 自定义表名（Custom Memory Table Names）

### 通过数据库配置

```python
from agno.db.mysql import MySQLDb

db = MySQLDb(
    db_url="mysql+pymysql://user:password@host:port",
    db_schema="agno_demo",
    memory_table="custom_memories",  # 自定义记忆表名
)
```

### 表名规则

| 配置 | 表名 |
|------|------|
| 无配置 | `agno_memories` |
| 设置 `db_schema` | `{db_schema}_memories` |
| 设置 `memory_table` | 使用自定义表名 |

---

## 记忆和上下文（Memories and Context）

### 配置选项

```python
agent = Agent(
    db=db,
    user_id="user-123",
    
    # 记忆相关
    enable_user_memories=True,     # 启用记忆
    add_memories_to_context=True,  # 将记忆添加到上下文
    
    # 会话历史相关
    add_history_to_context=True,   # 添加会话历史到上下文
    num_history_runs=5,            # 添加的历史运行数量
)
```

### 两者区别

| 特性 | 记忆 (Memory) | 会话历史 (Session History) |
|------|--------------|---------------------------|
| 持久性 | 长期持久化 | 会话级别 |
| 内容 | 用户事实和偏好 | 对话消息 |
| 跨会话 | ✅ 是 | ❌ 否 |
| 启用参数 | `enable_user_memories` | `add_history_to_context` |

---

## 数据库配置

### 支持的数据库

| 数据库 | 类 | 适用场景 |
|--------|-----|----------|
| MySQL | `MySQLDb` | 生产环境 |
| PostgreSQL | `PostgresDb` | 生产环境 |
| SQLite | `SqliteDb` | 开发环境 |
| Redis | `RedisDb` | 高性能缓存 |
| MongoDB | `MongoDb` | NoSQL场景 |

### 配置示例

```python
# MySQL
from agno.db.mysql import MySQLDb
db = MySQLDb(
    db_url="mysql+pymysql://user:password@host:port",
    db_schema="agno_demo",
)

# PostgreSQL
from agno.db.postgres import PostgresDb
db = PostgresDb(db_url="postgresql://user:password@host:port/database")

# SQLite
from agno.db.sqlite import SqliteDb
db = SqliteDb(db_file="agno.db")

# MongoDB
from agno.db.mongo import MongoDb
db = MongoDb(
    connection_string="mongodb://localhost:27017",
    database_name="agno_db",
)
```

---

## 具有记忆的智能体（Agents with Memory）

### 完整示例

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager

# 1. 设置数据库
db = SqliteDb(db_file="agno.db")

# 2. 创建自定义记忆管理器（可选）
memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-4o-mini"),
    memory_capture_instructions="Only store user preferences",
)

# 3. 创建具有记忆的智能体
agent = Agent(
    name="PersonalAssistant",
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    user_id="user-123",
    
    # 记忆配置
    enable_user_memories=True,
    add_memories_to_context=True,
    memory_manager=memory_manager,
    
    # 会话历史配置
    add_history_to_context=True,
    num_history_runs=5,
    
    instructions=["You are a helpful personal assistant"],
    markdown=True,
)

# 4. 使用智能体
agent.print_response("My name is John and I prefer dark mode")
agent.print_response("What's my name and preference?")

# 5. 手动检索记忆
memories = agent.get_user_memories(user_id="user-123")
for m in memories:
    print(f"- {m.memory} (topics: {m.topics})")
```

---

## 常见问题

### Q1: 记忆没有被存储？
**检查清单**：
1. ✅ 是否设置了 `enable_user_memories=True` 或 `enable_agentic_memory=True`？
2. ✅ 是否配置了 `db` 参数？
3. ✅ 是否设置了 `user_id`？
4. ✅ 数据库连接是否正常？

### Q2: enable_user_memories 和 enable_agentic_memory 有什么区别？
- **enable_user_memories**: 自动记忆模式，智能体自动提取和存储信息
- **enable_agentic_memory**: 智能体控制模式，智能体通过工具主动管理记忆
- 两者互斥，只能启用其中一个

### Q3: 如何控制记忆的内容？
使用 `MemoryManager` 的指令参数：
```python
memory_manager = MemoryManager(
    db=db,
    memory_capture_instructions="Only store preferences, not personal details",
    additional_instructions="Don't store sensitive information",
)
```

### Q4: 如何在多智能体之间共享记忆？
确保所有智能体：
1. 连接到同一个数据库
2. 使用相同的 `user_id`
3. 使用相同的 `memory_table`（或默认表名）

### Q5: 如何清除用户的所有记忆？
```python
memory_manager = MemoryManager(db=db)
memory_manager.clear_user_memories(user_id="user-123")
```

### Q6: 如何优化大量记忆？
使用记忆优化策略：
```python
from agno.memory import MemoryManager, SummarizeOldest

memory_manager = MemoryManager(
    db=db,
    memory_optimization_strategy=SummarizeOldest(num_memories=100),
)
memory_manager.optimize_memories(user_id="user-123")
```

---

## 相关资源

- **Agno 官方文档 - Memory**: https://docs.agno.com/agents/memory
- **MemoryManager 参考**: https://docs.agno.com/reference/memory/memory
- **处理记忆指南**: https://docs.agno.com/basics/memory/working-with-memories/overview
