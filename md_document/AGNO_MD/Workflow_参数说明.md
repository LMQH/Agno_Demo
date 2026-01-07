# Workflow 参数说明文档

本文档详细说明了 Agno 框架中 `Workflow` 类的所有参数及其用途。

## 目录

- [基础设置](#基础设置)
- [工作流步骤](#工作流步骤)
- [数据库](#数据库)
- [智能工作流](#智能工作流)
- [会话设置](#会话设置)
- [调试设置](#调试设置)
- [流式输出](#流式输出)
- [输入验证](#输入验证)
- [元数据](#元数据)
- [历史记录](#历史记录)
- [遥测](#遥测)
- [其他参数](#其他参数)

---

## 基础设置

### `id`
- **类型**: `Optional[str]`
- **说明**: Workflow 的唯一标识符 (UUID)，如果未设置则自动生成。如果提供了 `name`，将基于 `name` 生成 ID（转换为小写并替换空格为连字符）
- **默认值**: `None`
- **示例**:
  ```python
  workflow = Workflow(id="my-workflow-123")
  ```

### `name`
- **类型**: `Optional[str]`
- **说明**: Workflow 的名称，用于标识和管理工作流
- **默认值**: `None`
- **示例**:
  ```python
  workflow = Workflow(name="数据处理工作流")
  ```

### `description`
- **类型**: `Optional[str]`
- **说明**: Workflow 的描述，说明其目的或功能
- **默认值**: `None`
- **示例**:
  ```python
  workflow = Workflow(
      name="数据处理工作流",
      description="用于处理和分析数据的多步骤工作流"
  )
  ```

---

## 工作流步骤

### `steps`
- **类型**: `Optional[WorkflowSteps]`
- **说明**: 工作流的步骤定义。可以是以下类型之一：
  - 可调用函数：`Callable[[Workflow, WorkflowExecutionInput], StepOutput]`
  - `Steps` 对象：包含多个步骤的容器
  - 步骤列表：`List[Union[Callable, Step, Steps, Loop, Parallel, Condition, Router]]`
- **默认值**: `None`
- **示例**:
  ```python
  # 使用函数
  async def my_workflow(session_state, execution_input):
      return {"output": "result"}
  
  workflow = Workflow(steps=my_workflow)
  
  # 使用步骤列表
  from agno.workflow.step import Step
  workflow = Workflow(steps=[
      Step(name="step1", executor=function1),
      Step(name="step2", executor=function2),
  ])
  ```

---

## 数据库

### `db`
- **类型**: `Optional[Union[BaseDb, AsyncBaseDb]]`
- **说明**: 用于此 Workflow 的数据库，用于存储工作流会话和运行历史
- **默认值**: `None`
- **注意**: 
  - 生产环境使用 `PostgresDb`
  - 开发环境可使用 `SqliteDb`
  - 如果启用 `add_workflow_history_to_steps`，必须配置数据库
- **示例**:
  ```python
  from agno.db.sqlite import SqliteDb
  from agno.db.postgres import PostgresDb
  
  # 开发环境
  workflow = Workflow(steps=my_workflow, db=SqliteDb(db_file="tmp/workflow.db"))
  
  # 生产环境
  workflow = Workflow(steps=my_workflow, db=PostgresDb(db_url=os.getenv("DATABASE_URL")))
  ```

---

## 智能工作流

### `agent`
- **类型**: `Optional[WorkflowAgent]`
- **说明**: 智能工作流 Agent，用于决定何时运行工作流。当设置此参数时，Workflow 将使用 Agent 来决定是否执行步骤
- **默认值**: `None`
- **示例**:
  ```python
  from agno.workflow.agent import WorkflowAgent
  from agno.models.openai import OpenAIChat
  
  agent = WorkflowAgent(
      model=OpenAIChat(id="gpt-4o"),
      instructions="决定何时执行工作流步骤"
  )
  
  workflow = Workflow(steps=my_workflow, agent=agent)
  ```

---

## 会话设置

### `session_id`
- **类型**: `Optional[str]`
- **说明**: 此 Workflow 使用的默认会话 ID，如果未设置则自动生成
- **默认值**: `None`
- **注意**: 会话 ID 用于在多次运行之间保持状态和上下文
- **示例**:
  ```python
  workflow = Workflow(steps=my_workflow, session_id="user-123-session")
  ```

### `user_id`
- **类型**: `Optional[str]`
- **说明**: 此 Workflow 使用的默认用户 ID
- **默认值**: `None`
- **示例**:
  ```python
  workflow = Workflow(steps=my_workflow, user_id="user-123")
  ```

### `session_state`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 默认会话状态（存储在数据库中，用于跨运行持久化）。可以在工作流步骤中访问和修改此状态
- **默认值**: `None`
- **示例**:
  ```python
  workflow = Workflow(
      steps=my_workflow,
      session_state={"counter": 0, "data": []}
  )
  ```

### `overwrite_db_session_state`
- **类型**: `bool`
- **说明**: 设置为 `True` 时，使用运行中提供的 `session_state` 覆盖存储的会话状态。默认行为是将当前会话状态与数据库中的会话状态合并
- **默认值**: `False`
- **注意**: 谨慎使用此选项，因为它会完全替换现有的会话状态

### `cache_session`
- **类型**: `bool`
- **说明**: 如果为 `True`，在内存中缓存当前 Workflow 会话以加快访问速度
- **默认值**: `False`
- **注意**: 启用缓存可以提高性能，但会占用更多内存

---

## 调试设置

### `debug_mode`
- **类型**: `Optional[bool]`
- **说明**: 如果为 `True`，工作流在调试模式下运行，会输出更详细的调试信息
- **默认值**: `False`
- **示例**:
  ```python
  workflow = Workflow(steps=my_workflow, debug_mode=True)
  ```

### `debug_level`
- **类型**: `Literal[1, 2]`
- **说明**: 调试级别，控制调试信息的详细程度
  - `1`: 基本调试信息
  - `2`: 详细调试信息
- **默认值**: `1`
- **示例**:
  ```python
  workflow = Workflow(steps=my_workflow, debug_level=2)
  ```

---

## 流式输出

### `stream`
- **类型**: `Optional[bool]`
- **说明**: 从 Workflow 流式传输响应。当设置为 `True` 时，`run()` 或 `arun()` 方法将返回事件迭代器而不是完整的响应对象
- **默认值**: `None`
- **注意**: 可以在运行时通过 `run()` 或 `arun()` 方法的 `stream` 参数覆盖此设置
- **示例**:
  ```python
  workflow = Workflow(steps=my_workflow, stream=True)
  
  # 流式执行
  async for event in await workflow.arun(input="开始", stream=True):
      print(event)
  ```

### `stream_events`
- **类型**: `bool`
- **说明**: 从 Workflow 流式传输中间步骤事件。启用后，可以在流中接收到每个步骤的执行事件
- **默认值**: `False`
- **示例**:
  ```python
  workflow = Workflow(steps=my_workflow, stream_events=True)
  ```

### `stream_executor_events`
- **类型**: `bool`
- **说明**: 流式传输执行器（agents/teams/functions）在步骤内的事件。当步骤使用 Agent 或 Team 作为执行器时，可以流式传输这些执行器的事件
- **默认值**: `True`
- **示例**:
  ```python
  workflow = Workflow(
      steps=my_workflow,
      stream_executor_events=True
  )
  ```

### `stream_intermediate_steps` (已弃用)
- **类型**: `bool`
- **说明**: 已弃用。使用 `stream_events` 代替
- **默认值**: `False`
- **注意**: 设置此参数会触发 `DeprecationWarning`，建议使用 `stream_events`

### `store_events`
- **类型**: `bool`
- **说明**: 在运行响应上持久化事件。启用后，所有事件将存储在 `WorkflowRunOutput.events` 中
- **默认值**: `False`
- **示例**:
  ```python
  workflow = Workflow(steps=my_workflow, store_events=True)
  result = await workflow.arun(input="开始")
  # 访问事件
  for event in result.events:
      print(event)
  ```

### `events_to_skip`
- **类型**: `Optional[List[Union[WorkflowRunEvent, RunEvent, TeamRunEvent]]]`
- **说明**: 在持久化事件时要跳过的事件列表。用于减少存储的事件数量或过滤特定类型的事件
- **默认值**: `None`（默认跳过 `RunEvent.run_content`）
- **示例**:
  ```python
  from agno.events import RunEvent
  
  workflow = Workflow(
      steps=my_workflow,
      store_events=True,
      events_to_skip=[RunEvent.run_content]
  )
  ```

### `store_executor_outputs`
- **类型**: `bool`
- **说明**: 控制是否在扁平化运行中存储执行器响应（agent/team 响应）。启用后，执行器的输出将包含在运行响应中
- **默认值**: `True`
- **示例**:
  ```python
  workflow = Workflow(
      steps=my_workflow,
      store_executor_outputs=True
  )
  ```

---

## 输入验证

### `input_schema`
- **类型**: `Optional[Type[BaseModel]]`
- **说明**: 提供输入模式以验证输入。使用 Pydantic 模型定义输入结构，Workflow 会在执行前验证输入是否符合模式
- **默认值**: `None`
- **示例**:
  ```python
  from pydantic import BaseModel
  from typing import Optional
  
  class WorkflowInput(BaseModel):
      query: str
      context: Optional[str] = None
      priority: int = 1
  
  workflow = Workflow(
      steps=my_workflow,
      input_schema=WorkflowInput,
  )
  
  # 输入会被自动验证
  result = await workflow.arun(input={
      "query": "测试",
      "context": "上下文",
      "priority": 2
  })
  ```

---

## 元数据

### `metadata`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 与此 Workflow 一起存储的元数据。可以用于存储自定义信息，如版本号、标签、配置等
- **默认值**: `None`
- **示例**:
  ```python
  workflow = Workflow(
      steps=my_workflow,
      metadata={
          "version": "1.0.0",
          "author": "John Doe",
          "tags": ["production", "data-processing"]
      }
  )
  ```

---

## 历史记录

### `add_workflow_history_to_steps`
- **类型**: `bool`
- **说明**: 如果为 `True`，将工作流历史添加到步骤中。启用后，步骤函数可以通过 `StepInput.get_workflow_history()` 访问历史运行记录
- **默认值**: `False`
- **注意**: 
  - 启用此功能需要配置数据库（`db` 参数）
  - 如果未配置数据库，会发出警告
- **示例**:
  ```python
  workflow = Workflow(
      steps=my_workflow,
      db=SqliteDb(db_file="tmp/workflow.db"),
      add_workflow_history_to_steps=True
  )
  
  # 在步骤函数中访问历史
  async def step_with_history(step_input):
      history = step_input.get_workflow_history(num_runs=3)
      # 使用历史记录...
      return {"output": "完成"}
  ```

### `num_history_runs`
- **类型**: `int`
- **说明**: 要包含在消息中的历史运行次数。当 `add_workflow_history_to_steps=True` 时，此参数控制返回多少条历史记录
- **默认值**: `3`
- **示例**:
  ```python
  workflow = Workflow(
      steps=my_workflow,
      db=SqliteDb(db_file="tmp/workflow.db"),
      add_workflow_history_to_steps=True,
      num_history_runs=5  # 返回最近 5 次运行的历史
  )
  ```

---

## 遥测

### `telemetry`
- **类型**: `bool`
- **说明**: `telemetry=True` 记录用于分析的最小遥测数据。这有助于改进 Workflow 并提供更好的支持
- **默认值**: `True`
- **注意**: 遥测数据仅包含使用统计信息，不包含敏感数据

---

## 其他参数

### `websocket_handler`
- **类型**: `Optional["WebSocketHandler"]`
- **说明**: WebSocket 处理器，用于实时事件流传输。通常由 AgentOS 自动设置，不需要手动配置
- **默认值**: `None`
- **注意**: 这是一个类属性，通常不在 `__init__` 中直接设置

### `_run_hooks_in_background`
- **类型**: `bool`
- **说明**: 如果为 `True`，将 hooks 作为 FastAPI 后台任务运行（非阻塞）。通常由 AgentOS 自动设置
- **默认值**: `False`
- **注意**: 这是一个内部参数，通常不需要手动设置

---

## 参数使用建议

### 基础工作流
```python
from agno.workflow.workflow import Workflow
from agno.db.sqlite import SqliteDb

async def simple_workflow(session_state, execution_input):
    input_str = execution_input.get_input_as_string()
    return {"output": f"处理了输入: {input_str}"}

workflow = Workflow(
    name="SimpleWorkflow",
    steps=simple_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
)
```

### 带输入验证的工作流
```python
from pydantic import BaseModel
from agno.workflow.workflow import Workflow

class WorkflowInput(BaseModel):
    query: str
    context: Optional[str] = None

workflow = Workflow(
    name="ValidatedWorkflow",
    steps=my_workflow,
    input_schema=WorkflowInput,
)
```

### 带会话状态的工作流
```python
workflow = Workflow(
    name="StatefulWorkflow",
    steps=my_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
    session_id="my-session",
    session_state={"counter": 0},
)
```

### 流式输出工作流
```python
workflow = Workflow(
    name="StreamingWorkflow",
    steps=my_workflow,
    stream=True,
    stream_events=True,
    stream_executor_events=True,
)
```

### 带历史记录的工作流
```python
workflow = Workflow(
    name="HistoricalWorkflow",
    steps=my_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
    add_workflow_history_to_steps=True,
    num_history_runs=5,
)
```

---

## 注意事项

1. **性能**: 不要在循环中创建 Workflow，应重用它们以提高性能
2. **数据库**: 生产环境使用 `PostgresDb`，开发环境可使用 `SqliteDb`
3. **会话状态**: 使用 `session_state` 在运行之间持久化数据
4. **异步数据库**: 如果使用异步数据库，必须使用 `arun()` 和 `aprint_response()` 而不是 `run()` 和 `print_response()`
5. **历史记录**: 启用 `add_workflow_history_to_steps` 需要配置数据库
6. **输入验证**: 使用 `input_schema` 可以确保输入符合预期格式
7. **流式输出**: 启用流式输出时，确保正确处理事件迭代器

---

## 参考

- [Agno 官方文档](https://docs.agno.com)
- Workflow 类源代码: `agno/workflow/workflow.py`
- [Agno Agent 参数文档](./Agno_Agent_Agent_Parameters.md)
- [Agno Team 参数文档](./Agno_Team_Team_Parameters.md)

