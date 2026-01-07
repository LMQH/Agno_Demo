# Agno Team 参数说明文档

本文档详细说明了 Agno 框架中 `Team` 类的所有参数及其用途。

## 目录

- [基础设置](#基础设置)
- [用户设置](#用户设置)
- [会话设置](#会话设置)
- [团队成员](#团队成员)
- [模型设置](#模型设置)
- [指令和描述](#指令和描述)
- [数据库](#数据库)
- [知识库 (Knowledge/RAG)](#知识库-knowledgerag)
- [工具 (Tools)](#工具-tools)
- [团队协调](#团队协调)
- [响应设置](#响应设置)
- [响应模型设置](#响应模型设置)
- [流式输出](#流式输出)
- [元数据](#元数据)
- [调试和遥测](#调试和遥测)

---

## 基础设置

### `name`
- **类型**: `Optional[str]`
- **说明**: Team 的名称，用于标识和管理团队
- **默认值**: `None`

### `id`
- **类型**: `Optional[str]`
- **说明**: Team 的唯一标识符 (UUID)，如果未设置则自动生成
- **默认值**: `None`

---

## 用户设置

### `user_id`
- **类型**: `Optional[str]`
- **说明**: 此 Team 使用的默认用户 ID
- **默认值**: `None`

---

## 会话设置

### `session_id`
- **类型**: `Optional[str]`
- **说明**: 此 Team 使用的默认会话 ID，如果未设置则自动生成
- **默认值**: `None`

### `session_state`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 默认会话状态（存储在数据库中，用于跨运行持久化）
- **默认值**: `None`

### `add_session_state_to_context`
- **类型**: `bool`
- **说明**: 设置为 `True` 时，将 `session_state` 添加到上下文中
- **默认值**: `False`

---

## 团队成员

### `members`
- **类型**: `List[Agent]`
- **说明**: 团队成员列表，每个成员都是一个独立的 Agent 实例，具有特定的职责和能力。每个成员 Agent 应该具有明确的角色（通过 `name` 或 `role` 参数设置）
- **默认值**: 无（必需参数）
- **注意**: 
  - Team 必须至少包含一个成员
  - 每个成员 Agent 的 `team_id` 会自动设置为当前 Team 的 ID
  - 成员 Agent 可以使用自己的模型、工具和知识库，这些会与 Team 级别的配置合并

---

## 模型设置

### `model`
- **类型**: `Optional[Model]`
- **说明**: 用于团队协调的模型。Team 使用此模型来决定任务分配和成员协调
- **默认值**: `None`
- **示例**: `OpenAIChat(id="gpt-4o")`
- **重要**: Team 需要一个模型来进行智能协调和任务分配

---

## 指令和描述

### `description`
- **类型**: `Optional[str]`
- **说明**: 对团队的简要描述，说明其目的或功能
- **默认值**: `None`

### `instructions`
- **类型**: `Optional[Union[str, List[str]]]`
- **说明**: Team 的指令列表，指导团队如何执行任务和协作。可以是一个字符串或字符串列表
- **默认值**: `None`
- **示例**: 
  ```python
  instructions="Research and write articles"
  # 或
  instructions=["高效协作，首先进行信息检索", "然后基于检索结果进行总结报告"]
  ```

### `expected_output`
- **类型**: `Optional[str]`
- **说明**: 提供 Team 的预期输出描述
- **默认值**: `None`

### `markdown`
- **类型**: `bool`
- **说明**: 如果为 `True`，添加使用 markdown 格式化输出的指令
- **默认值**: `False`

---

## 数据库

### `db`
- **类型**: `Optional[Union[BaseDb, AsyncBaseDb]]`
- **说明**: 用于此 Team 的数据库，用于存储团队会话和运行历史
- **默认值**: `None`
- **注意**: 生产环境使用 `PostgresDb`，开发环境可使用 `SqliteDb`

---

## 知识库 (Knowledge/RAG)

### `knowledge`
- **类型**: `Optional[Knowledge]`
- **说明**: 团队共享的知识库对象，所有成员都可以访问
- **默认值**: `None`

### `add_knowledge_to_context`
- **类型**: `bool`
- **说明**: 通过将知识库的引用添加到上下文中来启用 RAG
- **默认值**: `False`
- **重要**: 启用 RAG 时，通常需要将此设置为 `True`

---

## 工具 (Tools)

### `tools`
- **类型**: `Optional[List[Union[Toolkit, Callable, Function, Dict]]]`
- **说明**: 团队级别的工具列表，所有成员都可以使用这些工具
- **默认值**: `None`
- **注意**: 成员 Agent 也可以有自己的工具，团队工具会与成员工具合并

### `tool_call_limit`
- **类型**: `Optional[int]`
- **说明**: 允许的最大工具调用次数（针对整个 Team）
- **默认值**: `None`

---

## 团队协调

### `show_members_responses`
- **类型**: `bool`
- **说明**: 如果为 `True`，在响应中显示每个成员的响应内容，便于调试和理解团队内部的交互
- **默认值**: `False`

### `enable_agentic_context`
- **类型**: `bool`
- **说明**: 如果为 `True`，允许团队在运行时动态更新会话状态，增强团队的适应性和灵活性
- **默认值**: `False`

### `num_iterations`
- **类型**: `Optional[int]`
- **说明**: Team 执行的最大迭代次数（成员之间的交互轮数）
- **默认值**: `None`

### `enable_reflections`
- **类型**: `bool`
- **说明**: 如果为 `True`，Team 会在成员响应后进行反思，以改进后续的协调决策
- **默认值**: `False`

---

## 响应设置

### `retries`
- **类型**: `int`
- **说明**: 重试次数
- **默认值**: `0`

### `delay_between_retries`
- **类型**: `int`
- **说明**: 重试之间的延迟（秒）
- **默认值**: `1`

### `exponential_backoff`
- **类型**: `bool`
- **说明**: 指数退避：如果为 `True`，每次重试之间的延迟会翻倍
- **默认值**: `False`

---

## 响应模型设置

### `output_schema`
- **类型**: `Optional[Type[BaseModel]]`
- **说明**: 提供响应模型以将响应作为 Pydantic 模型获取
- **默认值**: `None`
- **示例**: 
  ```python
  from pydantic import BaseModel
  class TeamResult(BaseModel):
      summary: str
      findings: list[str]
  team = Team(output_schema=TeamResult)
  ```

### `structured_outputs`
- **类型**: `Optional[bool]`
- **说明**: 如果支持，使用模型强制的结构化输出（例如 `OpenAIChat`）
- **默认值**: `None`

---

## 流式输出

### `stream`
- **类型**: `Optional[bool]`
- **说明**: 从 Team 流式传输响应
- **默认值**: `None`

### `stream_events`
- **类型**: `Optional[bool]`
- **说明**: 从 Team 流式传输中间步骤，包括成员之间的交互
- **默认值**: `None`

### `store_events`
- **类型**: `bool`
- **说明**: 在运行响应上持久化事件
- **默认值**: `False`

---

## 元数据

### `metadata`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 与此 Team 一起存储的元数据
- **默认值**: `None`

---

## 调试和遥测

### `debug_mode`
- **类型**: `bool`
- **说明**: 启用调试日志
- **默认值**: `False`

### `debug_level`
- **类型**: `Literal[1, 2]`
- **说明**: 调试级别（1 或 2）
- **默认值**: `1`

### `telemetry`
- **类型**: `bool`
- **说明**: `telemetry=True` 记录用于分析的最小遥测数据。这有助于我们改进 Team 并提供更好的支持
- **默认值**: `True`

---

## 使用示例

### 基础 Team

```python
from agno.team.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

web_agent = Agent(
    name="Researcher",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
)

writer_agent = Agent(
    name="Writer",
    model=OpenAIChat(id="gpt-4o"),
)

team = Team(
    members=[web_agent, writer_agent],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Research and write articles",
)
```

### 带知识库的 Team

```python
from agno.team.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.knowledge.embedder.openai import OpenAIEmbedder

knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="knowledge_base",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

researcher = Agent(
    name="Researcher",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
)

writer = Agent(
    name="Writer",
    model=OpenAIChat(id="gpt-4o"),
)

team = Team(
    name="Research Team",
    members=[researcher, writer],
    model=OpenAIChat(id="gpt-4o"),
    knowledge=knowledge,
    add_knowledge_to_context=True,
    instructions="Use knowledge base for research and writing",
)
```

### 带调试和流式输出的 Team

```python
team = Team(
    members=[web_agent, writer_agent],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Research and write articles",
    show_members_responses=True,  # 显示成员响应
    debug_mode=True,  # 启用调试
    stream=True,  # 启用流式输出
    markdown=True,  # Markdown 格式化
)
```

### 结构化输出的 Team

```python
from pydantic import BaseModel

class ArticleResult(BaseModel):
    title: str
    content: str
    sources: list[str]

team = Team(
    members=[researcher, writer],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Research and write articles",
    output_schema=ArticleResult,
)

result: ArticleResult = team.run(query).content
```

### 带数据库持久化的 Team

```python
from agno.db.sqlite import SqliteDb

team = Team(
    members=[web_agent, writer_agent],
    model=OpenAIChat(id="gpt-4o"),
    instructions="Research and write articles",
    db=SqliteDb(db_file="tmp/team.db"),
    user_id="user-123",
)
```

---

## Team 与 Agent 的区别

### 何时使用 Team

Team 适用于以下场景：
- **多智能体协作**：需要多个具有不同专长的 Agent 协同工作
- **复杂任务分解**：任务可以分解为多个子任务，由不同 Agent 处理
- **自主协调**：Team 使用 LLM 自动决定任务分配和成员协作
- **多阶段处理**：需要多个阶段处理的任务（如：研究 → 分析 → 写作）

### 何时使用单个 Agent

单个 Agent 适用于：
- **单一任务**：任务可以由一个 Agent 完成
- **工具组合**：使用工具和指令就能解决问题
- **简单工作流**：简单的顺序处理流程

---

## 注意事项

1. **性能**: 不要在循环中创建 Team，应重用它们以提高性能
2. **成员配置**: 确保每个成员 Agent 都有明确的角色和职责
3. **模型要求**: Team 需要一个协调模型（`model` 参数）来进行智能任务分配
4. **指令清晰**: 提供清晰的 `instructions` 有助于团队更好地协作
5. **数据库**: 生产环境使用 `PostgresDb`，开发环境可使用 `SqliteDb`
6. **调试**: 使用 `show_members_responses=True` 可以查看团队成员的具体响应，有助于调试和优化

---

## Team 工作流程

Team 的基本工作流程：

1. **接收任务**: Team 接收用户查询
2. **协调决策**: 使用协调模型（`model`）分析任务，决定如何分配给成员
3. **任务执行**: 成员 Agent 执行分配的任务
4. **结果整合**: Team 整合各成员的结果
5. **返回响应**: 返回最终响应给用户

---

## 参考

- [Agno 官方文档](https://docs.agno.com)
- Team 类源代码: `agno/team/team.py`
- [Agno Agent 参数文档](./Agno_Agent_Agent_Parameters.md)

