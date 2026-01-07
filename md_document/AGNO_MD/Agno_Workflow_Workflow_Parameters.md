# Agno Workflow 参数说明文档

本文档详细说明了 Agno 框架中 `Workflow` 类的所有参数及其用途，以及相关函数的使用方法。

## 目录

- [基础设置](#基础设置)
- [工作流步骤](#工作流步骤)
- [数据库](#数据库)
- [智能工作流](#智能工作流)
- [会话设置](#会话设置)
- [流式输出](#流式输出)
- [输入验证](#输入验证)
- [元数据](#元数据)
- [历史记录](#历史记录)
- [调试和遥测](#调试和遥测)
- [主要方法](#主要方法)
- [会话管理方法](#会话管理方法)
- [类型定义](#类型定义)
- [使用示例](#使用示例)

---

## 基础设置

### `name`
- **类型**: `Optional[str]`
- **说明**: Workflow 的名称，用于标识和管理工作流
- **默认值**: `None`

### `id`
- **类型**: `Optional[str]`
- **说明**: Workflow 的唯一标识符 (UUID)，如果未设置则自动生成
- **默认值**: `None`

### `description`
- **类型**: `Optional[str]`
- **说明**: Workflow 的描述，说明其目的或功能
- **默认值**: `None`

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
- **注意**: 生产环境使用 `PostgresDb`，开发环境可使用 `SqliteDb`

---

## 智能工作流

### `agent`
- **类型**: `Optional[WorkflowAgent]`
- **说明**: 智能工作流 Agent，用于决定何时运行工作流。当设置此参数时，Workflow 将使用 Agent 来决定是否执行步骤
- **默认值**: `None`

---

## 会话设置

### `session_id`
- **类型**: `Optional[str]`
- **说明**: 此 Workflow 使用的默认会话 ID，如果未设置则自动生成
- **默认值**: `None`

### `user_id`
- **类型**: `Optional[str]`
- **说明**: 此 Workflow 使用的默认用户 ID
- **默认值**: `None`

### `session_state`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 默认会话状态（存储在数据库中，用于跨运行持久化）
- **默认值**: `None`

### `overwrite_db_session_state`
- **类型**: `bool`
- **说明**: 设置为 `True` 时，使用运行中提供的 `session_state` 覆盖存储的会话状态。默认行为是将当前会话状态与数据库中的会话状态合并
- **默认值**: `False`

### `cache_session`
- **类型**: `bool`
- **说明**: 如果为 `True`，在内存中缓存当前 Workflow 会话以加快访问速度
- **默认值**: `False`

---

## 流式输出

### `stream`
- **类型**: `Optional[bool]`
- **说明**: 从 Workflow 流式传输响应
- **默认值**: `None`

### `stream_events`
- **类型**: `bool`
- **说明**: 从 Workflow 流式传输中间步骤事件
- **默认值**: `False`

### `stream_executor_events`
- **类型**: `bool`
- **说明**: 流式传输执行器（agents/teams/functions）在步骤内的事件
- **默认值**: `True`

### `store_events`
- **类型**: `bool`
- **说明**: 在运行响应上持久化事件
- **默认值**: `False`

### `events_to_skip`
- **类型**: `Optional[List[Union[WorkflowRunEvent, RunEvent, TeamRunEvent]]]`
- **说明**: 在持久化事件时要跳过的事件列表
- **默认值**: `None`（默认跳过 `RunEvent.run_content`）

### `store_executor_outputs`
- **类型**: `bool`
- **说明**: 控制是否在扁平化运行中存储执行器响应（agent/team 响应）
- **默认值**: `True`

### `stream_intermediate_steps` (已弃用)
- **类型**: `bool`
- **说明**: 已弃用。使用 `stream_events` 代替
- **默认值**: `False`

---

## 输入验证

### `input_schema`
- **类型**: `Optional[Type[BaseModel]]`
- **说明**: 提供输入模式以验证输入。使用 Pydantic 模型定义输入结构
- **默认值**: `None`
- **示例**:
  ```python
  from pydantic import BaseModel
  
  class WorkflowInput(BaseModel):
      query: str
      context: Optional[str] = None
  
  workflow = Workflow(
      steps=my_workflow,
      input_schema=WorkflowInput,
  )
  ```

---

## 元数据

### `metadata`
- **类型**: `Optional[Dict[str, Any]]`
- **说明**: 与此 Workflow 一起存储的元数据
- **默认值**: `None`

---

## 历史记录

### `add_workflow_history_to_steps`
- **类型**: `bool`
- **说明**: 如果为 `True`，将工作流历史添加到步骤中
- **默认值**: `False`
- **注意**: 启用此功能需要配置数据库（`db` 参数）

### `num_history_runs`
- **类型**: `int`
- **说明**: 要包含在消息中的历史运行次数
- **默认值**: `3`

---

## 调试和遥测

### `debug_mode`
- **类型**: `Optional[bool]`
- **说明**: 如果为 `True`，工作流在调试模式下运行
- **默认值**: `False`

### `debug_level`
- **类型**: `Literal[1, 2]`
- **说明**: 调试级别（1 或 2）
- **默认值**: `1`

### `telemetry`
- **类型**: `bool`
- **说明**: `telemetry=True` 记录用于分析的最小遥测数据。这有助于我们改进 Workflow 并提供更好的支持
- **默认值**: `True`

---

## 主要方法

### `run()`
同步执行工作流。

**签名**:
```python
def run(
    self,
    input: Optional[Union[str, Dict[str, Any], List[Any], BaseModel]] = None,
    additional_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    session_id: Optional[str] = None,
    session_state: Optional[Dict[str, Any]] = None,
    audio: Optional[List[Audio]] = None,
    images: Optional[List[Image]] = None,
    videos: Optional[List[Video]] = None,
    files: Optional[List[File]] = None,
    stream: bool = False,
    stream_events: Optional[bool] = None,
    stream_intermediate_steps: Optional[bool] = None,
    background: Optional[bool] = False,
    background_tasks: Optional[Any] = None,
) -> Union[WorkflowRunOutput, Iterator[WorkflowRunOutputEvent]]
```

**参数**:
- `input`: 工作流的主要输入（字符串、字典、列表或 Pydantic 模型）
- `additional_data`: 附加到输入的数据
- `user_id`: 用户 ID
- `run_id`: 运行 ID（如果未提供则自动生成）
- `session_id`: 会话 ID
- `session_state`: 会话状态字典
- `audio`: 音频输入列表
- `images`: 图像输入列表
- `videos`: 视频输入列表
- `files`: 文件输入列表
- `stream`: 是否流式传输响应
- `stream_events`: 是否流式传输事件
- `stream_intermediate_steps`: 是否流式传输中间步骤（已弃用）
- `background`: 是否在后台运行（同步模式下不支持）
- `background_tasks`: 后台任务列表

**返回**:
- 如果 `stream=False`: 返回 `WorkflowRunOutput`
- 如果 `stream=True`: 返回 `Iterator[WorkflowRunOutputEvent]`

**注意**: 如果使用异步数据库，此方法不可用，请使用 `arun()`。

### `arun()`
异步执行工作流。

**签名**:
```python
async def arun(
    self,
    input: Optional[Union[str, Dict[str, Any], List[Any], BaseModel, List[Message]]] = None,
    additional_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    session_id: Optional[str] = None,
    session_state: Optional[Dict[str, Any]] = None,
    audio: Optional[List[Audio]] = None,
    images: Optional[List[Image]] = None,
    videos: Optional[List[Video]] = None,
    files: Optional[List[File]] = None,
    stream: bool = False,
    stream_events: Optional[bool] = None,
    stream_intermediate_steps: Optional[bool] = False,
    background: Optional[bool] = False,
    websocket: Optional[WebSocket] = None,
    background_tasks: Optional[Any] = None,
) -> Union[WorkflowRunOutput, AsyncIterator[WorkflowRunOutputEvent]]
```

**参数**:
- 与 `run()` 相同的参数，额外包括：
- `websocket`: WebSocket 连接（用于实时事件流）

**返回**:
- 如果 `stream=False`: 返回 `WorkflowRunOutput`
- 如果 `stream=True`: 返回 `AsyncIterator[WorkflowRunOutputEvent]`

### `print_response()`
同步打印工作流执行结果，带有丰富的格式化和可选的流式传输。

**签名**:
```python
def print_response(
    self,
    input: Union[str, Dict[str, Any], List[Any], BaseModel, List[Message]],
    additional_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    audio: Optional[List[Audio]] = None,
    images: Optional[List[Image]] = None,
    videos: Optional[List[Video]] = None,
    files: Optional[List[File]] = None,
    stream: Optional[bool] = None,
    markdown: bool = True,
    show_time: bool = True,
    show_step_details: bool = True,
    console: Optional[Any] = None,
) -> None
```

**参数**:
- `input`: 工作流的主要输入
- `additional_data`: 附加数据
- `user_id`: 用户 ID
- `session_id`: 会话 ID
- `audio`: 音频输入
- `images`: 图像输入
- `videos`: 视频输入
- `files`: 文件输入
- `stream`: 是否流式传输响应
- `markdown`: 是否将内容渲染为 markdown
- `show_time`: 是否显示执行时间
- `show_step_details`: 是否显示各个步骤的输出
- `console`: Rich console 实例（可选）

**注意**: 如果使用异步数据库，此方法不可用，请使用 `aprint_response()`。

### `aprint_response()`
异步打印工作流执行结果，带有丰富的格式化和可选的流式传输。

**签名**:
```python
async def aprint_response(
    self,
    input: Union[str, Dict[str, Any], List[Any], BaseModel, List[Message]],
    additional_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    audio: Optional[List[Audio]] = None,
    images: Optional[List[Image]] = None,
    videos: Optional[List[Video]] = None,
    files: Optional[List[File]] = None,
    stream: Optional[bool] = None,
    markdown: bool = True,
    show_time: bool = True,
    show_step_details: bool = True,
    console: Optional[Any] = None,
) -> None
```

**参数**: 与 `print_response()` 相同

---

## 会话管理方法

### `get_session()`
从数据库加载 WorkflowSession。

**签名**:
```python
def get_session(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowSession]
```

### `aget_session()`
异步从数据库加载 WorkflowSession。

**签名**:
```python
async def aget_session(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowSession]
```

### `save_session()`
将会话保存到存储。

**签名**:
```python
def save_session(self, session: WorkflowSession) -> None
```

### `asave_session()`
异步将会话保存到存储。

**签名**:
```python
async def asave_session(self, session: WorkflowSession) -> None
```

### `get_session_state()`
获取给定会话 ID 的会话状态。

**签名**:
```python
def get_session_state(self, session_id: Optional[str] = None) -> Dict[str, Any]
```

### `aget_session_state()`
异步获取给定会话 ID 的会话状态。

**签名**:
```python
async def aget_session_state(self, session_id: Optional[str] = None) -> Dict[str, Any]
```

### `update_session_state()`
更新给定会话 ID 的会话状态。

**签名**:
```python
def update_session_state(
    self,
    session_state_updates: Dict[str, Any],
    session_id: Optional[str] = None,
) -> Dict[str, Any]
```

### `aupdate_session_state()`
异步更新给定会话 ID 的会话状态。

**签名**:
```python
async def aupdate_session_state(
    self,
    session_state_updates: Dict[str, Any],
    session_id: Optional[str] = None,
) -> Dict[str, Any]
```

### `get_chat_history()`
返回会话中每次运行的输入和输出列表。

**签名**:
```python
def get_chat_history(
    self,
    session_id: Optional[str] = None,
    last_n_runs: Optional[int] = None,
) -> List[WorkflowChatInteraction]
```

### `aget_chat_history()`
异步返回会话中每次运行的输入和输出列表。

**签名**:
```python
async def aget_chat_history(
    self,
    session_id: Optional[str] = None,
    last_n_runs: Optional[int] = None,
) -> List[WorkflowChatInteraction]
```

### `get_run_output()`
从数据库获取 RunOutput。

**签名**:
```python
def get_run_output(
    self,
    run_id: str,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

### `aget_run_output()`
异步从数据库获取 RunOutput。

**签名**:
```python
async def aget_run_output(
    self,
    run_id: str,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

### `get_last_run_output()`
从数据库获取最后一次运行响应。

**签名**:
```python
def get_last_run_output(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

### `aget_last_run_output()`
异步从数据库获取最后一次运行响应。

**签名**:
```python
async def aget_last_run_output(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

### `set_session_name()`
设置会话名称并保存到存储。

**签名**:
```python
def set_session_name(
    self,
    session_id: Optional[str] = None,
    autogenerate: bool = False,
    session_name: Optional[str] = None,
) -> WorkflowSession
```

### `aset_session_name()`
异步设置会话名称并保存到存储。

**签名**:
```python
async def aset_session_name(
    self,
    session_id: Optional[str] = None,
    autogenerate: bool = False,
    session_name: Optional[str] = None,
) -> WorkflowSession
```

### `get_session_name()`
获取给定会话 ID 的会话名称。

**签名**:
```python
def get_session_name(self, session_id: Optional[str] = None) -> str
```

### `aget_session_name()`
异步获取给定会话 ID 的会话名称。

**签名**:
```python
async def aget_session_name(self, session_id: Optional[str] = None) -> str
```

### `delete_session()`
删除当前会话。

**签名**:
```python
def delete_session(self, session_id: str) -> None
```

### `adelete_session()`
异步删除当前会话。

**签名**:
```python
async def adelete_session(self, session_id: str) -> None
```

### `run_parameters`
属性：获取工作流的运行参数。

**类型**: `Dict[str, Any]`

**说明**: 返回工作流步骤函数的参数信息，包括参数名称、默认值、类型注解和是否必需。

---

## 类型定义

### `WorkflowExecutionInput`
工作流执行输入数据类。

**字段**:
- `input`: `Optional[Union[str, Dict[str, Any], List[Any], BaseModel]]` - 主要输入
- `additional_data`: `Optional[Dict[str, Any]]` - 附加数据
- `images`: `Optional[List[Image]]` - 图像输入
- `videos`: `Optional[List[Video]]` - 视频输入
- `audio`: `Optional[List[Audio]]` - 音频输入
- `files`: `Optional[List[File]]` - 文件输入

**方法**:
- `get_input_as_string() -> Optional[str]`: 将输入转换为字符串表示

### `StepInput`
步骤执行输入数据类。

**字段**:
- `input`: `Optional[Union[str, Dict[str, Any], List[Any], BaseModel]]` - 主要输入
- `previous_step_content`: `Optional[Any]` - 前一步的内容
- `previous_step_outputs`: `Optional[Dict[str, StepOutput]]` - 前一步的输出
- `additional_data`: `Optional[Dict[str, Any]]` - 附加数据
- `images`: `Optional[List[Image]]` - 图像输入
- `videos`: `Optional[List[Video]]` - 视频输入
- `audio`: `Optional[List[Audio]]` - 音频输入
- `files`: `Optional[List[File]]` - 文件输入
- `workflow_session`: `Optional[WorkflowSession]` - 工作流会话

**方法**:
- `get_input_as_string() -> Optional[str]`: 将输入转换为字符串
- `get_step_output(step_name: str) -> Optional[StepOutput]`: 获取特定前一步的输出
- `get_step_content(step_name: str) -> Optional[Union[str, Dict[str, str]]]`: 获取特定前一步的内容
- `get_all_previous_content() -> str`: 获取所有前一步的拼接内容
- `get_last_step_content() -> Optional[str]`: 获取最近一步的内容
- `get_workflow_history(num_runs: Optional[int] = None) -> List[Tuple[str, str]]`: 获取工作流对话历史
- `get_workflow_history_context(num_runs: Optional[int] = None) -> Optional[str]`: 获取格式化的工作流对话历史上下文

### `StepOutput`
步骤执行输出数据类。

**字段**:
- `step_name`: `Optional[str]` - 步骤名称
- `step_id`: `Optional[str]` - 步骤 ID
- `step_type`: `Optional[str]` - 步骤类型
- `executor_type`: `Optional[str]` - 执行器类型
- `executor_name`: `Optional[str]` - 执行器名称
- `content`: `Optional[Union[str, Dict[str, Any], List[Any], BaseModel, Any]]` - 主要输出
- `step_run_id`: `Optional[str]` - 步骤运行的 ID
- `images`: `Optional[List[Image]]` - 图像输出
- `videos`: `Optional[List[Video]]` - 视频输出
- `audio`: `Optional[List[Audio]]` - 音频输出
- `files`: `Optional[List[File]]` - 文件输出
- `metrics`: `Optional[Metrics]` - 此步骤执行的指标
- `success`: `bool` - 是否成功
- `error`: `Optional[str]` - 错误信息
- `stop`: `bool` - 是否停止
- `steps`: `Optional[List[StepOutput]]` - 嵌套步骤输出

**方法**:
- `to_dict() -> Dict[str, Any]`: 转换为字典
- `from_dict(data: Dict[str, Any]) -> StepOutput`: 从字典创建 StepOutput

### `StepType`
步骤类型枚举。

**值**:
- `FUNCTION`: "Function"
- `STEP`: "Step"
- `STEPS`: "Steps"
- `LOOP`: "Loop"
- `PARALLEL`: "Parallel"
- `CONDITION`: "Condition"
- `ROUTER`: "Router"

---

## 使用示例

### 基础 Workflow

```python
from agno.workflow.workflow import Workflow
from agno.db.sqlite import SqliteDb

async def simple_workflow(session_state, execution_input):
    """简单的工作流函数"""
    input_str = execution_input.get_input_as_string()
    return {"output": f"处理了输入: {input_str}"}

workflow = Workflow(
    name="SimpleWorkflow",
    steps=simple_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
)

# 运行工作流
result = await workflow.arun(input="Hello, World!")
print(result.content)
```

### 带多个步骤的 Workflow

```python
from agno.workflow.step import Step
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# 定义步骤函数
async def step1(step_input):
    return {"result": "步骤1完成"}

async def step2(step_input):
    previous = step_input.get_last_step_content()
    return {"result": f"步骤2完成，基于: {previous}"}

# 创建 Agent 步骤
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="你是一个助手",
)

workflow = Workflow(
    name="MultiStepWorkflow",
    steps=[
        Step(name="step1", executor=step1),
        Step(name="step2", executor=step2),
        Step(name="agent_step", agent=agent),
    ],
    db=SqliteDb(db_file="tmp/workflow.db"),
)

result = await workflow.arun(input="开始工作流")
```

### 带输入验证的 Workflow

```python
from pydantic import BaseModel
from agno.workflow.workflow import Workflow

class WorkflowInput(BaseModel):
    query: str
    context: Optional[str] = None

async def validated_workflow(session_state, execution_input):
    # execution_input.input 已经是验证过的 WorkflowInput 实例
    input_data = execution_input.input
    return {"output": f"查询: {input_data.query}"}

workflow = Workflow(
    name="ValidatedWorkflow",
    steps=validated_workflow,
    input_schema=WorkflowInput,
)

result = await workflow.arun(input={"query": "测试", "context": "上下文"})
```

### 带会话状态的 Workflow

```python
async def stateful_workflow(session_state, execution_input):
    # 访问会话状态
    counter = session_state.get("counter", 0)
    counter += 1
    session_state["counter"] = counter
    
    return {"output": f"这是第 {counter} 次运行"}

workflow = Workflow(
    name="StatefulWorkflow",
    steps=stateful_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
    session_id="my-session",
)

# 第一次运行
result1 = await workflow.arun(input="开始")
print(result1.content)  # 这是第 1 次运行

# 第二次运行（会话状态会保留）
result2 = await workflow.arun(input="继续")
print(result2.content)  # 这是第 2 次运行
```

### 流式输出 Workflow

```python
async def streaming_workflow(session_state, execution_input):
    for i in range(5):
        yield {"step": i, "output": f"步骤 {i}"}

workflow = Workflow(
    name="StreamingWorkflow",
    steps=streaming_workflow,
    stream=True,
    stream_events=True,
)

# 流式执行
async for event in await workflow.arun(input="开始", stream=True):
    print(event)
```

### 使用 print_response 的 Workflow

```python
workflow = Workflow(
    name="PrintableWorkflow",
    steps=my_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
)

# 打印响应（带格式化）
await workflow.aprint_response(
    input="处理这个任务",
    stream=True,
    markdown=True,
    show_time=True,
    show_step_details=True,
)
```

### 带历史记录的 Workflow

```python
workflow = Workflow(
    name="HistoricalWorkflow",
    steps=my_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
    add_workflow_history_to_steps=True,
    num_history_runs=5,
)

# 在步骤函数中访问历史
async def step_with_history(step_input):
    history = step_input.get_workflow_history(num_runs=3)
    context = step_input.get_workflow_history_context(num_runs=3)
    # 使用历史记录...
    return {"output": "完成"}
```

---

## Workflow 与 Agent/Team 的区别

### 何时使用 Workflow

Workflow 适用于以下场景：
- **程序化控制**：需要明确的顺序步骤和条件逻辑
- **复杂流程**：需要分支、循环、并行执行等控制流
- **数据管道**：ETL（提取、转换、加载）类型的任务
- **多阶段处理**：需要按顺序处理多个阶段的任务
- **状态管理**：需要在步骤之间传递和持久化状态

### 何时使用 Agent

单个 Agent 适用于：
- **单一任务**：任务可以由一个 Agent 完成
- **工具组合**：使用工具和指令就能解决问题
- **简单交互**：简单的问答或任务执行

### 何时使用 Team

Team 适用于：
- **多智能体协作**：需要多个具有不同专长的 Agent 协同工作
- **自主协调**：Team 使用 LLM 自动决定任务分配和成员协作
- **复杂任务分解**：任务可以分解为多个子任务，由不同 Agent 处理

---

## 注意事项

1. **性能**: 不要在循环中创建 Workflow，应重用它们以提高性能
2. **数据库**: 生产环境使用 `PostgresDb`，开发环境可使用 `SqliteDb`
3. **会话状态**: 使用 `session_state` 在运行之间持久化数据
4. **异步数据库**: 如果使用异步数据库，必须使用 `arun()` 和 `aprint_response()` 而不是 `run()` 和 `print_response()`
5. **流式输出**: 启用流式输出时，确保正确处理事件迭代器
6. **步骤函数签名**: 自定义步骤函数应接受 `session_state` 和 `execution_input` 参数（或 `step_input` 对于 Step 对象）
7. **历史记录**: 启用 `add_workflow_history_to_steps` 需要配置数据库
8. **输入验证**: 使用 `input_schema` 可以确保输入符合预期格式

---

## 工作流执行流程

Workflow 的基本执行流程：

1. **初始化**: 设置工作流 ID 和会话
2. **输入验证**: 如果提供了 `input_schema`，验证输入
3. **会话加载**: 从数据库加载或创建会话
4. **状态初始化**: 初始化会话状态（合并数据库状态和运行参数）
5. **步骤准备**: 准备步骤列表（包装可调用函数等）
6. **执行步骤**: 按顺序执行步骤，传递前一步的输出
7. **状态保存**: 保存会话状态到数据库
8. **返回结果**: 返回 `WorkflowRunOutput` 或事件流

---

## 参考

- [Agno 官方文档](https://docs.agno.com)
- Workflow 类源代码: `agno/workflow/workflow.py`
- [Agno Agent 参数文档](./Agno_Agent_Agent_Parameters.md)
- [Agno Team 参数文档](./Agno_Team_Team_Parameters.md)

