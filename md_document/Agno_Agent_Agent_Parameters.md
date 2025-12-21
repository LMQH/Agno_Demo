# Agno Agent 参数说明文档

本文档详细说明了 Agno 框架中 `Agent` 类的所有参数及其用途。

## 目录

- [基础设置](#基础设置)
- [用户设置](#用户设置)
- [会话设置](#会话设置)
- [代理依赖](#代理依赖)
- [代理记忆](#代理记忆)
- [数据库](#数据库)
- [历史记录](#历史记录)
- [知识库 (Knowledge/RAG)](#知识库-knowledgerag)
- [工具 (Tools)](#工具-tools)
- [代理钩子 (Hooks)](#代理钩子-hooks)
- [推理 (Reasoning)](#推理-reasoning)
- [默认工具](#默认工具)
- [系统消息设置](#系统消息设置)
- [额外消息](#额外消息)
- [用户消息设置](#用户消息设置)
- [响应设置](#响应设置)
- [响应模型设置](#响应模型设置)
- [流式输出](#流式输出)
- [团队和工作流](#团队和工作流)
- [元数据](#元数据)
- [实验性功能](#实验性功能)
- [调试和遥测](#调试和遥测)

---

## 基础设置

### `model`
- **类型**: `Optional[Model]`
- **说明**: 用于此 Agent 的模型
- **默认值**: `None`
- **示例**: `OpenAIChat(id="gpt-4o")`

### `name`
- **类型**: `Optional[str]`
- **说明**: Agent 的名称
- **默认值**: `None`

### `id`
- **类型**: `Optional[str]`
- **说明**: Agent 的唯一标识符 (UUID)，如果未设置则自动生成
- **默认值**: `None`

---

## 用户设置

### `user_id`
- **类型**: `Optional[str]`
- **说明**: 此 Agent 使用的默认用户 ID
- **默认值**: `None`

---

## 会话设置

### `session_id`
- **类型**: `Optional[str]`
- **说明**: 此 Agent 使用的默认会话 ID，如果未设置则自动生成
- **默认值**: `None`

### `session_state`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 默认会话状态（存储在数据库中，用于跨运行持久化）
- **默认值**: `None`

### `add_session_state_to_context`
- **类型**: `bool`
- **说明**: 设置为 `True` 时，将 `session_state` 添加到上下文中
- **默认值**: `False`

### `enable_agentic_state`
- **类型**: `bool`
- **说明**: 设置为 `True` 时，为 Agent 提供动态更新 `session_state` 的工具
- **默认值**: `False`

### `overwrite_db_session_state`
- **类型**: `bool`
- **说明**: 设置为 `True` 时，使用运行中提供的 `session_state` 覆盖存储的会话状态。默认行为是将当前会话状态与数据库中的会话状态合并
- **默认值**: `False`

### `cache_session`
- **类型**: `bool`
- **说明**: 如果为 `True`，在内存中缓存当前 Agent 会话以加快访问速度
- **默认值**: `False`

### `search_session_history`
- **类型**: `Optional[bool]`
- **说明**: 是否搜索会话历史
- **默认值**: `False`

### `num_history_sessions`
- **类型**: `Optional[int]`
- **说明**: 要包含的历史会话数量
- **默认值**: `None`

### `enable_session_summaries`
- **类型**: `bool`
- **说明**: 如果为 `True`，Agent 在运行结束时创建/更新会话摘要
- **默认值**: `False`

### `add_session_summary_to_context`
- **类型**: `Optional[bool]`
- **说明**: 如果为 `True`，Agent 将会话摘要添加到上下文中
- **默认值**: `None`

### `session_summary_manager`
- **类型**: `Optional[SessionSummaryManager]`
- **说明**: 会话摘要管理器
- **默认值**: `None`

---

## 代理依赖

### `dependencies`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 可用于工具和提示函数的依赖项
- **默认值**: `None`

### `add_dependencies_to_context`
- **类型**: `bool`
- **说明**: 如果为 `True`，将依赖项添加到用户提示中
- **默认值**: `False`

---

## 代理记忆

### `memory_manager`
- **类型**: `Optional[MemoryManager]`
- **说明**: 用于此 Agent 的记忆管理器
- **默认值**: `None`

### `enable_agentic_memory`
- **类型**: `bool`
- **说明**: 启用 Agent 管理用户记忆的功能
- **默认值**: `False`

### `enable_user_memories`
- **类型**: `bool`
- **说明**: 如果为 `True`，Agent 在运行结束时创建/更新用户记忆
- **默认值**: `False`

### `add_memories_to_context`
- **类型**: `Optional[bool]`
- **说明**: 如果为 `True`，Agent 在响应中添加对用户记忆的引用
- **默认值**: `None`

---

## 数据库

### `db`
- **类型**: `Optional[Union[BaseDb, AsyncBaseDb]]`
- **说明**: 用于此 Agent 的数据库
- **默认值**: `None`
- **注意**: 生产环境使用 `PostgresDb`，开发环境可使用 `SqliteDb`

---

## 历史记录

### `add_history_to_context`
- **类型**: `bool`
- **说明**: 设置为 `True` 时，将聊天历史中的消息添加到发送给模型的消息列表中
- **默认值**: `False`

### `num_history_runs`
- **类型**: `Optional[int]`
- **说明**: 要包含在消息中的历史运行次数
- **默认值**: `None`（如果 `num_history_messages` 也为 `None`，则默认为 `3`）

### `num_history_messages`
- **类型**: `Optional[int]`
- **说明**: 要包含在发送给模型的消息列表中的历史消息数量
- **默认值**: `None`
- **注意**: 不能与 `num_history_runs` 同时设置

### `max_tool_calls_from_history`
- **类型**: `Optional[int]`
- **说明**: 从历史记录中包含的最大工具调用数（`None` = 无限制）
- **默认值**: `None`

---

## 知识库 (Knowledge/RAG)

### `knowledge`
- **类型**: `Optional[Knowledge]`
- **说明**: 知识库对象
- **默认值**: `None`

### `knowledge_filters`
- **类型**: `Optional[Union[Dict[str, Any], List[FilterExpr]]]`
- **说明**: 知识库过滤器
- **默认值**: `None`

### `enable_agentic_knowledge_filters`
- **类型**: `Optional[bool]`
- **说明**: 让 Agent 选择知识过滤器
- **默认值**: `False`

### `add_knowledge_to_context`
- **类型**: `bool`
- **说明**: 通过将知识库的引用添加到用户提示中来启用 RAG
- **默认值**: `False`
- **重要**: 启用 RAG 时，通常需要将此设置为 `True`

### `knowledge_retriever`
- **类型**: `Optional[Callable[..., Optional[List[Union[Dict, str]]]]]`
- **说明**: 用于获取引用的检索函数。如果提供，将使用此函数代替默认的 `search_knowledge` 函数
- **函数签名**:
  ```python
  def knowledge_retriever(agent: Agent, query: str, num_documents: Optional[int], **kwargs) -> Optional[list[dict]]:
      ...
  ```
- **默认值**: `None`

### `references_format`
- **类型**: `Literal["json", "yaml"]`
- **说明**: 引用格式
- **默认值**: `"json"`

---

## 工具 (Tools)

### `tools`
- **类型**: `Optional[List[Union[Toolkit, Callable, Function, Dict]]]`
- **说明**: 提供给模型的工具列表。工具是模型可能为其生成 JSON 输入的函数
- **默认值**: `None`

### `tool_call_limit`
- **类型**: `Optional[int]`
- **说明**: 允许的最大工具调用次数
- **默认值**: `None`

### `tool_choice`
- **类型**: `Optional[Union[str, Dict[str, Any]]]`
- **说明**: 控制模型调用哪个（如果有）工具
  - `"none"`: 模型不会调用工具，而是生成消息
  - `"auto"`: 模型可以在生成消息或调用工具之间选择
  - `{"type": "function", "function": {"name": "my_function"}}`: 强制模型调用特定工具
- **默认值**: 
  - 没有工具时为 `"none"`
  - 有工具时为 `"auto"`

### `tool_hooks`
- **类型**: `Optional[List[Callable]]`
- **说明**: 作为中间件在工具调用周围调用的函数列表
- **默认值**: `None`

---

## 代理钩子 (Hooks)

### `pre_hooks`
- **类型**: `Optional[List[Union[Callable[..., Any], BaseGuardrail]]]`
- **说明**: 在加载 Agent 会话后、处理开始前调用的函数列表
- **默认值**: `None`

### `post_hooks`
- **类型**: `Optional[List[Union[Callable[..., Any], BaseGuardrail]]]`
- **说明**: 在生成输出后、返回响应前调用的函数列表
- **默认值**: `None`

---

## 推理 (Reasoning)

### `reasoning`
- **类型**: `bool`
- **说明**: 通过逐步解决问题来启用推理
- **默认值**: `False`

### `reasoning_model`
- **类型**: `Optional[Model]`
- **说明**: 用于推理的模型
- **默认值**: `None`

### `reasoning_agent`
- **类型**: `Optional[Agent]`
- **说明**: 用于推理的 Agent
- **默认值**: `None`

### `reasoning_min_steps`
- **类型**: `int`
- **说明**: 推理的最小步骤数
- **默认值**: `1`

### `reasoning_max_steps`
- **类型**: `int`
- **说明**: 推理的最大步骤数
- **默认值**: `10`

---

## 默认工具

### `read_chat_history`
- **类型**: `bool`
- **说明**: 添加一个允许模型读取聊天历史的工具
- **默认值**: `False`

### `search_knowledge`
- **类型**: `bool`
- **说明**: 添加一个允许模型搜索知识库的工具（也称为 Agentic RAG）。仅在提供 `knowledge` 时添加
- **默认值**: `True`

### `update_knowledge`
- **类型**: `bool`
- **说明**: 添加一个允许 Agent 更新知识库的工具
- **默认值**: `False`

### `read_tool_call_history`
- **类型**: `bool`
- **说明**: 添加一个允许模型获取工具调用历史的工具
- **默认值**: `False`

### `send_media_to_model`
- **类型**: `bool`
- **说明**: 如果为 `False`，媒体（图像、视频、音频、文件）仅对工具可用，不会发送给 LLM
- **默认值**: `True`

### `store_media`
- **类型**: `bool`
- **说明**: 如果为 `True`，在运行输出中存储媒体
- **默认值**: `True`

### `store_tool_messages`
- **类型**: `bool`
- **说明**: 如果为 `True`，在运行输出中存储工具消息
- **默认值**: `True`

### `store_history_messages`
- **类型**: `bool`
- **说明**: 如果为 `True`，在运行输出中存储历史消息
- **默认值**: `True`

---

## 系统消息设置

### `system_message`
- **类型**: `Optional[Union[str, Callable, Message]]`
- **说明**: 以字符串、函数或 Message 对象形式提供系统消息
- **默认值**: `None`

### `system_message_role`
- **类型**: `str`
- **说明**: 系统消息的角色
- **默认值**: `"system"`

### `build_context`
- **类型**: `bool`
- **说明**: 设置为 `False` 以跳过上下文构建
- **默认值**: `True`

### `description`
- **类型**: `Optional[str]`
- **说明**: Agent 的描述，添加到系统消息的开头
- **默认值**: `None`

### `instructions`
- **类型**: `Optional[Union[str, List[str], Callable]]`
- **说明**: Agent 的指令列表
- **默认值**: `None`

### `expected_output`
- **类型**: `Optional[str]`
- **说明**: 提供 Agent 的预期输出
- **默认值**: `None`

### `additional_context`
- **类型**: `Optional[str]`
- **说明**: 添加到系统消息末尾的额外上下文
- **默认值**: `None`

### `markdown`
- **类型**: `bool`
- **说明**: 如果为 `True`，添加使用 markdown 格式化输出的指令
- **默认值**: `False`

### `add_name_to_context`
- **类型**: `bool`
- **说明**: 如果为 `True`，将 Agent 名称添加到指令中
- **默认值**: `False`

### `add_datetime_to_context`
- **类型**: `bool`
- **说明**: 如果为 `True`，将当前日期时间添加到指令中，使 Agent 具有时间感。这允许在提示中使用相对时间，如"明天"
- **默认值**: `False`

### `add_location_to_context`
- **类型**: `bool`
- **说明**: 如果为 `True`，将当前位置添加到指令中，使 Agent 具有位置感。这允许位置感知响应和本地上下文
- **默认值**: `False`

### `timezone_identifier`
- **类型**: `Optional[str]`
- **说明**: 允许为日期时间指令自定义时区，遵循 TZ 数据库格式（例如 `"Etc/UTC"`）
- **默认值**: `None`

### `resolve_in_context`
- **类型**: `bool`
- **说明**: 如果为 `True`，在用户和系统消息中解析 `session_state`、`dependencies` 和 `metadata`
- **默认值**: `True`

---

## 额外消息

### `additional_input`
- **类型**: `Optional[List[Union[str, Dict, BaseModel, Message]]]`
- **说明**: 在系统消息之后、用户消息之前添加的额外消息列表。用于少样本学习或向模型提供额外上下文
- **注意**: 这些消息不会保留在内存中，它们直接添加到发送给模型的消息中
- **默认值**: `None`

---

## 用户消息设置

### `user_message_role`
- **类型**: `str`
- **说明**: 用户消息的角色
- **默认值**: `"user"`

### `build_user_context`
- **类型**: `bool`
- **说明**: 设置为 `False` 以跳过构建用户上下文
- **默认值**: `True`

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

### `input_schema`
- **类型**: `Optional[Type[BaseModel]]`
- **说明**: 提供输入模式以验证输入
- **默认值**: `None`

### `output_schema`
- **类型**: `Optional[Type[BaseModel]]`
- **说明**: 提供响应模型以将响应作为 Pydantic 模型获取
- **默认值**: `None`
- **示例**: 
  ```python
  from pydantic import BaseModel
  class Result(BaseModel):
      summary: str
      findings: list[str]
  agent = Agent(output_schema=Result)
  ```

### `parser_model`
- **类型**: `Optional[Model]`
- **说明**: 提供辅助模型以从主模型解析响应
- **默认值**: `None`

### `parser_model_prompt`
- **类型**: `Optional[str]`
- **说明**: 为解析器模型提供提示
- **默认值**: `None`

### `output_model`
- **类型**: `Optional[Model]`
- **说明**: 提供输出模型以构建主模型的响应
- **默认值**: `None`

### `output_model_prompt`
- **类型**: `Optional[str]`
- **说明**: 为输出模型提供提示
- **默认值**: `None`

### `parse_response`
- **类型**: `bool`
- **说明**: 如果为 `True`，将模型的响应转换为 `output_schema`。否则，响应作为 JSON 字符串返回
- **默认值**: `True`

### `structured_outputs`
- **类型**: `Optional[bool]`
- **说明**: 如果支持，使用模型强制的结构化输出（例如 `OpenAIChat`）
- **默认值**: `None`

### `use_json_mode`
- **类型**: `bool`
- **说明**: 如果设置了 `output_schema`，设置模型的响应模式，即模型是否应该显式响应 JSON 对象而不是 Pydantic 模型
- **默认值**: `False`

### `save_response_to_file`
- **类型**: `Optional[str]`
- **说明**: 将响应保存到文件
- **默认值**: `None`

---

## 流式输出

### `stream`
- **类型**: `Optional[bool]`
- **说明**: 从 Agent 流式传输响应
- **默认值**: `None`

### `stream_events`
- **类型**: `Optional[bool]`
- **说明**: 从 Agent 流式传输中间步骤
- **默认值**: `None`

### `store_events`
- **类型**: `bool`
- **说明**: 在运行响应上持久化事件
- **默认值**: `False`

### `events_to_skip`
- **类型**: `Optional[List[RunEvent]]`
- **说明**: 要跳过的事件列表
- **默认值**: `None`（默认跳过 `RunEvent.run_content`）

### `stream_intermediate_steps` (已弃用)
- **类型**: `Optional[bool]`
- **说明**: 已弃用。使用 `stream_events` 代替
- **默认值**: `None`

---

## 团队和工作流

### `role`
- **类型**: `Optional[str]`
- **说明**: 如果此 Agent 是团队的一部分，这是 Agent 在团队中的角色
- **默认值**: `None`

### `team_id`
- **类型**: `Optional[str]`
- **说明**: 可选的团队 ID。表示此 Agent 是团队的一部分
- **默认值**: `None`

### `workflow_id`
- **类型**: `Optional[str]`
- **说明**: 可选的工作流 ID。表示此 Agent 是工作流的一部分
- **默认值**: `None`

---

## 元数据

### `metadata`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 与此 Agent 一起存储的元数据
- **默认值**: `None`

---

## 实验性功能

### `culture_manager`
- **类型**: `Optional[CultureManager]`
- **说明**: 用于此 Agent 的文化管理器
- **默认值**: `None`

### `enable_agentic_culture`
- **类型**: `bool`
- **说明**: 启用 Agent 管理文化知识
- **默认值**: `False`

### `update_cultural_knowledge`
- **类型**: `bool`
- **说明**: 每次运行后更新文化知识
- **默认值**: `False`

### `add_culture_to_context`
- **类型**: `Optional[bool]`
- **说明**: 如果为 `True`，Agent 在响应中添加文化知识
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
- **说明**: `telemetry=True` 记录用于分析的最小遥测数据。这有助于我们改进 Agent 并提供更好的支持
- **默认值**: `True`

---

## 使用示例

### 基础 Agent

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant",
    markdown=True,
)
agent.print_response("Your query", stream=True)
```

### 带工具的 Agent

```python
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    instructions="Search the web for information",
)
```

### 带知识库的 Agent (RAG)

```python
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

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    knowledge=knowledge,
    search_knowledge=True,  # 关键：启用 agentic RAG
    add_knowledge_to_context=True,  # 将知识添加到上下文
    instructions="Use knowledge base, cite sources"
)
```

### 带聊天历史的 Agent

```python
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="tmp/agents.db"),
    user_id="user-123",
    add_history_to_context=True,  # 添加上下文中的先前消息
    num_history_runs=3,
)
```

### 结构化输出

```python
from pydantic import BaseModel

class Result(BaseModel):
    summary: str
    findings: list[str]

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    output_schema=Result,
)
result: Result = agent.run(query).content
```

---

## 注意事项

1. **性能**: 不要在循环中创建 Agent，应重用它们以提高性能
2. **数据库**: 生产环境使用 `PostgresDb`，开发环境可使用 `SqliteDb`
3. **知识库**: 使用知识库时，确保设置 `add_knowledge_to_context=True` 和 `search_knowledge=True`
4. **历史记录**: `num_history_messages` 和 `num_history_runs` 不能同时设置
5. **结构化输出**: 使用 `output_schema` 时，响应会自动验证和解析

---

## 参考

- [Agno 官方文档](https://docs.agno.com)
- Agent 类源代码: `agno/agent/agent.py`

