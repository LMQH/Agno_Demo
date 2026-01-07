# Workflow 相关函数说明文档

本文档详细说明了 Agno 框架中 `Workflow` 类的所有公共方法及其用途。

## 目录

- [执行方法](#执行方法)
- [会话管理方法](#会话管理方法)
- [会话状态方法](#会话状态方法)
- [运行输出方法](#运行输出方法)
- [历史记录方法](#历史记录方法)
- [指标方法](#指标方法)
- [工具方法](#工具方法)
- [属性](#属性)

---

## 执行方法

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

**注意**: 
- 如果使用异步数据库，此方法不可用，请使用 `arun()`
- 同步模式下不支持后台执行

**示例**:
```python
# 同步执行
result = workflow.run(input="处理这个任务")
print(result.content)

# 流式执行
for event in workflow.run(input="处理这个任务", stream=True):
    print(event)
```

---

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

**注意**: 
- 支持后台执行和 WebSocket 流式传输
- 如果 `background=True` 且 `stream=True`，必须提供 `websocket` 参数

**示例**:
```python
# 异步执行
result = await workflow.arun(input="处理这个任务")
print(result.content)

# 异步流式执行
async for event in await workflow.arun(input="处理这个任务", stream=True):
    print(event)

# 后台执行（带 WebSocket）
async for event in await workflow.arun(
    input="处理这个任务",
    background=True,
    stream=True,
    websocket=websocket
):
    await websocket.send_json(event.dict())
```

---

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
- `stream`: 是否流式传输响应（如果为 `None`，使用工作流默认设置）
- `markdown`: 是否将内容渲染为 markdown
- `show_time`: 是否显示执行时间
- `show_step_details`: 是否显示各个步骤的输出
- `console`: Rich console 实例（可选）

**注意**: 如果使用异步数据库，此方法不可用，请使用 `aprint_response()`

**示例**:
```python
workflow.print_response(
    input="处理这个任务",
    stream=True,
    markdown=True,
    show_time=True,
    show_step_details=True
)
```

---

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

**示例**:
```python
await workflow.aprint_response(
    input="处理这个任务",
    stream=True,
    markdown=True,
    show_time=True,
    show_step_details=True
)
```

---

### `cancel_run()`

取消正在运行的工作流执行。

**签名**:
```python
def cancel_run(self, run_id: str) -> bool
```

**参数**:
- `run_id`: 要取消的运行 ID

**返回**:
- `bool`: 如果运行被找到并标记为取消，返回 `True`，否则返回 `False`

**示例**:
```python
# 启动一个运行
run_id = "run-123"
workflow.run(input="长时间运行的任务", run_id=run_id)

# 取消运行
if workflow.cancel_run(run_id):
    print("运行已取消")
```

---

## 会话管理方法

### `get_session()`

从数据库加载 WorkflowSession（同步）。

**签名**:
```python
def get_session(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowSession]
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `Optional[WorkflowSession]`: 会话对象，如果未找到则返回 `None`

**示例**:
```python
session = workflow.get_session(session_id="my-session")
if session:
    print(f"会话名称: {session.session_data.get('session_name')}")
```

---

### `aget_session()`

异步从数据库加载 WorkflowSession。

**签名**:
```python
async def aget_session(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowSession]
```

**参数**: 与 `get_session()` 相同

**返回**: 与 `get_session()` 相同

**示例**:
```python
session = await workflow.aget_session(session_id="my-session")
if session:
    print(f"会话名称: {session.session_data.get('session_name')}")
```

---

### `save_session()`

将会话保存到存储（同步）。

**签名**:
```python
def save_session(self, session: WorkflowSession) -> None
```

**参数**:
- `session`: 要保存的 WorkflowSession 对象

**示例**:
```python
session = workflow.get_session(session_id="my-session")
if session:
    session.session_data["custom_key"] = "custom_value"
    workflow.save_session(session)
```

---

### `asave_session()`

异步将会话保存到存储。

**签名**:
```python
async def asave_session(self, session: WorkflowSession) -> None
```

**参数**: 与 `save_session()` 相同

**示例**:
```python
session = await workflow.aget_session(session_id="my-session")
if session:
    session.session_data["custom_key"] = "custom_value"
    await workflow.asave_session(session)
```

---

### `read_or_create_session()`

读取或创建会话（同步）。

**签名**:
```python
def read_or_create_session(
    self,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> WorkflowSession
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用默认会话 ID）
- `user_id`: 用户 ID（如果未提供，使用默认用户 ID）

**返回**:
- `WorkflowSession`: 会话对象（如果不存在则创建）

**示例**:
```python
session = workflow.read_or_create_session(
    session_id="my-session",
    user_id="user-123"
)
```

---

### `aread_or_create_session()`

异步读取或创建会话。

**签名**:
```python
async def aread_or_create_session(
    self,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> WorkflowSession
```

**参数**: 与 `read_or_create_session()` 相同

**返回**: 与 `read_or_create_session()` 相同

**示例**:
```python
session = await workflow.aread_or_create_session(
    session_id="my-session",
    user_id="user-123"
)
```

---

### `delete_session()`

删除当前会话（同步）。

**签名**:
```python
def delete_session(self, session_id: str) -> None
```

**参数**:
- `session_id`: 要删除的会话 ID

**示例**:
```python
workflow.delete_session(session_id="my-session")
```

---

### `adelete_session()`

异步删除当前会话。

**签名**:
```python
async def adelete_session(self, session_id: str) -> None
```

**参数**: 与 `delete_session()` 相同

**示例**:
```python
await workflow.adelete_session(session_id="my-session")
```

---

### `set_session_name()`

设置会话名称并保存到存储（同步）。

**签名**:
```python
def set_session_name(
    self,
    session_id: Optional[str] = None,
    autogenerate: bool = False,
    session_name: Optional[str] = None,
) -> WorkflowSession
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）
- `autogenerate`: 如果为 `True`，自动生成会话名称
- `session_name`: 要设置的会话名称（如果 `autogenerate=True`，则忽略）

**返回**:
- `WorkflowSession`: 更新后的会话对象

**示例**:
```python
# 手动设置名称
session = workflow.set_session_name(
    session_id="my-session",
    session_name="我的工作流会话"
)

# 自动生成名称
session = workflow.set_session_name(
    session_id="my-session",
    autogenerate=True
)
```

---

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

**参数**: 与 `set_session_name()` 相同

**返回**: 与 `set_session_name()` 相同

**示例**:
```python
session = await workflow.aset_session_name(
    session_id="my-session",
    session_name="我的工作流会话"
)
```

---

### `get_session_name()`

获取给定会话 ID 的会话名称（同步）。

**签名**:
```python
def get_session_name(self, session_id: Optional[str] = None) -> str
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `str`: 会话名称，如果未找到则返回空字符串

**示例**:
```python
name = workflow.get_session_name(session_id="my-session")
print(f"会话名称: {name}")
```

---

### `aget_session_name()`

异步获取给定会话 ID 的会话名称。

**签名**:
```python
async def aget_session_name(self, session_id: Optional[str] = None) -> str
```

**参数**: 与 `get_session_name()` 相同

**返回**: 与 `get_session_name()` 相同

**示例**:
```python
name = await workflow.aget_session_name(session_id="my-session")
print(f"会话名称: {name}")
```

---

## 会话状态方法

### `get_session_state()`

获取给定会话 ID 的会话状态（同步）。

**签名**:
```python
def get_session_state(self, session_id: Optional[str] = None) -> Dict[str, Any]
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `Dict[str, Any]`: 会话状态字典

**示例**:
```python
state = workflow.get_session_state(session_id="my-session")
print(f"计数器: {state.get('counter', 0)}")
```

---

### `aget_session_state()`

异步获取给定会话 ID 的会话状态。

**签名**:
```python
async def aget_session_state(self, session_id: Optional[str] = None) -> Dict[str, Any]
```

**参数**: 与 `get_session_state()` 相同

**返回**: 与 `get_session_state()` 相同

**示例**:
```python
state = await workflow.aget_session_state(session_id="my-session")
print(f"计数器: {state.get('counter', 0)}")
```

---

### `update_session_state()`

更新给定会话 ID 的会话状态（同步）。

**签名**:
```python
def update_session_state(
    self,
    session_state_updates: Dict[str, Any],
    session_id: Optional[str] = None,
) -> Dict[str, Any]
```

**参数**:
- `session_state_updates`: 要应用到会话状态的更新（键值对字典）
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `Dict[str, Any]`: 更新后的会话状态

**示例**:
```python
updated_state = workflow.update_session_state(
    session_state_updates={"counter": 5, "last_action": "processed"},
    session_id="my-session"
)
print(f"更新后的状态: {updated_state}")
```

---

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

**参数**: 与 `update_session_state()` 相同

**返回**: 与 `update_session_state()` 相同

**示例**:
```python
updated_state = await workflow.aupdate_session_state(
    session_state_updates={"counter": 5, "last_action": "processed"},
    session_id="my-session"
)
print(f"更新后的状态: {updated_state}")
```

---

## 运行输出方法

### `get_run_output()`

从数据库获取 RunOutput（同步）。

**签名**:
```python
def get_run_output(
    self,
    run_id: str,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

**参数**:
- `run_id`: 运行 ID
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `Optional[WorkflowRunOutput]`: 运行输出对象，如果未找到则返回 `None`

**示例**:
```python
run_output = workflow.get_run_output(
    run_id="run-123",
    session_id="my-session"
)
if run_output:
    print(f"运行内容: {run_output.content}")
```

---

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

**参数**: 与 `get_run_output()` 相同

**返回**: 与 `get_run_output()` 相同

**示例**:
```python
run_output = await workflow.aget_run_output(
    run_id="run-123",
    session_id="my-session"
)
if run_output:
    print(f"运行内容: {run_output.content}")
```

---

### `get_last_run_output()`

从数据库获取最后一次运行响应（同步）。

**签名**:
```python
def get_last_run_output(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `Optional[WorkflowRunOutput]`: 最后一次运行输出对象，如果未找到则返回 `None`

**示例**:
```python
last_run = workflow.get_last_run_output(session_id="my-session")
if last_run:
    print(f"最后一次运行内容: {last_run.content}")
```

---

### `aget_last_run_output()`

异步从数据库获取最后一次运行响应。

**签名**:
```python
async def aget_last_run_output(
    self,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

**参数**: 与 `get_last_run_output()` 相同

**返回**: 与 `get_last_run_output()` 相同

**示例**:
```python
last_run = await workflow.aget_last_run_output(session_id="my-session")
if last_run:
    print(f"最后一次运行内容: {last_run.content}")
```

---

### `get_run()`

获取后台工作流运行的状态和详细信息（同步）。

**签名**:
```python
def get_run(
    self,
    run_id: str,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

**参数**:
- `run_id`: 运行 ID
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `Optional[WorkflowRunOutput]`: 运行输出对象，如果未找到则返回 `None`

**注意**: 此方法主要用于获取后台运行的状态

**示例**:
```python
# 启动后台运行
run_id = "run-123"
await workflow.arun(input="任务", background=True, run_id=run_id)

# 检查运行状态
run = workflow.get_run(run_id=run_id, session_id="my-session")
if run:
    print(f"运行状态: {run.status}")
```

---

### `aget_run()`

异步获取后台工作流运行的状态和详细信息。

**签名**:
```python
async def aget_run(
    self,
    run_id: str,
    session_id: Optional[str] = None,
) -> Optional[WorkflowRunOutput]
```

**参数**: 与 `get_run()` 相同

**返回**: 与 `get_run()` 相同

**示例**:
```python
run = await workflow.aget_run(run_id="run-123", session_id="my-session")
if run:
    print(f"运行状态: {run.status}")
```

---

## 历史记录方法

### `get_chat_history()`

返回会话中每次运行的输入和输出列表（同步）。

**签名**:
```python
def get_chat_history(
    self,
    session_id: Optional[str] = None,
    last_n_runs: Optional[int] = None,
) -> List[WorkflowChatInteraction]
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）
- `last_n_runs`: 要包含的最近运行次数。如果为 `None`，将包含所有运行

**返回**:
- `List[WorkflowChatInteraction]`: WorkflowChatInteraction 对象列表

**示例**:
```python
history = workflow.get_chat_history(
    session_id="my-session",
    last_n_runs=5
)
for interaction in history:
    print(f"输入: {interaction.input}")
    print(f"输出: {interaction.output}")
```

---

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

**参数**: 与 `get_chat_history()` 相同

**返回**: 与 `get_chat_history()` 相同

**示例**:
```python
history = await workflow.aget_chat_history(
    session_id="my-session",
    last_n_runs=5
)
for interaction in history:
    print(f"输入: {interaction.input}")
    print(f"输出: {interaction.output}")
```

---

## 指标方法

### `get_session_metrics()`

获取给定会话 ID 的会话指标（同步）。

**签名**:
```python
def get_session_metrics(
    self,
    session_id: Optional[str] = None,
) -> Optional[Metrics]
```

**参数**:
- `session_id`: 会话 ID（如果未提供，使用当前缓存的会话 ID）

**返回**:
- `Optional[Metrics]`: 会话指标对象，如果未找到则返回 `None`

**示例**:
```python
metrics = workflow.get_session_metrics(session_id="my-session")
if metrics:
    print(f"总 token 数: {metrics.total_tokens}")
    print(f"总成本: {metrics.total_cost}")
    print(f"执行时间: {metrics.time}")
```

---

### `aget_session_metrics()`

异步获取给定会话 ID 的会话指标。

**签名**:
```python
async def aget_session_metrics(
    self,
    session_id: Optional[str] = None,
) -> Optional[Metrics]
```

**参数**: 与 `get_session_metrics()` 相同

**返回**: 与 `get_session_metrics()` 相同

**示例**:
```python
metrics = await workflow.aget_session_metrics(session_id="my-session")
if metrics:
    print(f"总 token 数: {metrics.total_tokens}")
    print(f"总成本: {metrics.total_cost}")
    print(f"执行时间: {metrics.time}")
```

---

## 工具方法

### `to_dict()`

将工作流转换为字典表示。

**签名**:
```python
def to_dict(self) -> Dict[str, Any]
```

**返回**:
- `Dict[str, Any]`: 包含工作流信息的字典，包括：
  - `name`: 工作流名称
  - `workflow_id`: 工作流 ID
  - `description`: 工作流描述
  - `steps`: 步骤列表（序列化后的步骤信息）
  - `session_id`: 会话 ID

**示例**:
```python
workflow_dict = workflow.to_dict()
print(json.dumps(workflow_dict, indent=2))
```

---

### `cli_app()`

运行交互式命令行界面以与工作流交互（同步）。

**签名**:
```python
def cli_app(
    self,
    input: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user: str = "User",
    emoji: str = ":technologist:",
    stream: Optional[bool] = None,
    markdown: bool = True,
    show_time: bool = True,
    show_step_details: bool = True,
    exit_on: Optional[List[str]] = None,
    **kwargs: Any,
) -> None
```

**参数**:
- `input`: 可选的初始输入，在启动交互模式之前处理
- `session_id`: 可选的会话标识符，用于维护对话上下文
- `user_id`: 可选的用户标识符，用于跟踪用户特定数据
- `user`: CLI 提示中显示的用户显示名称，默认为 "User"
- `emoji`: 在提示中显示在用户名旁边的表情符号，默认为 ":technologist:"
- `stream`: 是否流式传输工作流响应。如果为 `None`，使用工作流默认设置
- `markdown`: 是否将输出渲染为 markdown，默认为 `True`
- `show_time`: 是否在输出中显示时间戳，默认为 `True`
- `show_step_details`: 是否显示详细的步骤信息，默认为 `True`
- `exit_on`: 将退出 CLI 的命令列表，默认为 `["exit", "quit", "bye", "stop"]`
- `**kwargs`: 传递给工作流的 `print_response` 方法的其他关键字参数

**返回**: `None`（此方法以交互方式运行，不返回值）

**示例**:
```python
# 启动交互式 CLI
workflow.cli_app(
    session_id="my-session",
    user_id="user-123",
    user="开发者",
    emoji=":rocket:"
)
```

---

### `acli_app()`

异步运行交互式命令行界面以与工作流交互。

**签名**:
```python
async def acli_app(
    self,
    input: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user: str = "User",
    emoji: str = ":technologist:",
    stream: Optional[bool] = None,
    markdown: bool = True,
    show_time: bool = True,
    show_step_details: bool = True,
    exit_on: Optional[List[str]] = None,
    **kwargs: Any,
) -> None
```

**参数**: 与 `cli_app()` 相同

**返回**: 与 `cli_app()` 相同

**示例**:
```python
await workflow.acli_app(
    session_id="my-session",
    user_id="user-123"
)
```

---

### `initialize_workflow()`

初始化工作流（设置 ID 等）。

**签名**:
```python
def initialize_workflow(self) -> None
```

**说明**: 如果工作流 ID 未设置，会自动生成。通常在 `run()` 或 `arun()` 内部调用。

**示例**:
```python
workflow = Workflow(steps=my_workflow)
workflow.initialize_workflow()
print(f"工作流 ID: {workflow.id}")
```

---

### `set_id()`

设置工作流 ID。

**签名**:
```python
def set_id(self) -> None
```

**说明**: 如果工作流 ID 未设置，基于 `name` 生成（转换为小写并替换空格为连字符），否则生成 UUID。

**示例**:
```python
workflow = Workflow(name="My Workflow")
workflow.set_id()
print(f"工作流 ID: {workflow.id}")  # 输出: "my-workflow"
```

---

### `update_agents_and_teams_session_info()`

更新工作流步骤中的 agents 和 teams 的会话信息。

**签名**:
```python
def update_agents_and_teams_session_info(self) -> None
```

**说明**: 将工作流 ID 传播到步骤中的所有 agents 和 teams，包括嵌套的 teams 及其成员。

**示例**:
```python
workflow.update_agents_and_teams_session_info()
```

---

### `propagate_run_hooks_in_background()`

将 `_run_hooks_in_background` 设置传播到此工作流和步骤中的所有 agents/teams。

**签名**:
```python
def propagate_run_hooks_in_background(self, run_in_background: bool = True) -> None
```

**参数**:
- `run_in_background`: 是否在后台运行 hooks

**说明**: 此方法设置工作流和所有 agents/teams 的 `_run_hooks_in_background` 标志，包括嵌套的 teams 及其成员。

**示例**:
```python
workflow.propagate_run_hooks_in_background(run_in_background=True)
```

---

## 属性

### `run_parameters`

属性：获取工作流的运行参数。

**类型**: `Dict[str, Any]`

**说明**: 返回工作流步骤函数的参数信息，包括参数名称、默认值、类型注解和是否必需。如果步骤是可调用函数，则分析其函数签名；否则返回默认的 `message` 参数。

**示例**:
```python
parameters = workflow.run_parameters
print(f"运行参数: {parameters}")
# 输出示例:
# {
#     "query": {
#         "name": "query",
#         "default": None,
#         "annotation": "str",
#         "required": True
#     },
#     "context": {
#         "name": "context",
#         "default": None,
#         "annotation": "str",
#         "required": False
#     }
# }
```

---

## 方法分类总结

### 同步 vs 异步方法

大多数方法都有同步和异步两个版本：
- 同步方法：`method_name()`
- 异步方法：`amethod_name()`

**选择指南**:
- 如果使用同步数据库（如 `SqliteDb`），使用同步方法
- 如果使用异步数据库（如 `PostgresDb`），使用异步方法
- 在异步上下文中，优先使用异步方法

### 方法命名模式

1. **执行方法**: `run()`, `arun()`, `print_response()`, `aprint_response()`, `cancel_run()`
2. **会话管理**: `get_session()`, `aget_session()`, `save_session()`, `asave_session()`, `read_or_create_session()`, `aread_or_create_session()`, `delete_session()`, `adelete_session()`
3. **会话名称**: `set_session_name()`, `aset_session_name()`, `get_session_name()`, `aget_session_name()`
4. **会话状态**: `get_session_state()`, `aget_session_state()`, `update_session_state()`, `aupdate_session_state()`
5. **运行输出**: `get_run_output()`, `aget_run_output()`, `get_last_run_output()`, `aget_last_run_output()`, `get_run()`, `aget_run()`
6. **历史记录**: `get_chat_history()`, `aget_chat_history()`
7. **指标**: `get_session_metrics()`, `aget_session_metrics()`
8. **工具**: `to_dict()`, `cli_app()`, `acli_app()`, `initialize_workflow()`, `set_id()`

---

## 使用示例

### 完整工作流示例

```python
from agno.workflow.workflow import Workflow
from agno.db.sqlite import SqliteDb

async def my_workflow(session_state, execution_input):
    input_str = execution_input.get_input_as_string()
    counter = session_state.get("counter", 0)
    counter += 1
    session_state["counter"] = counter
    return {"output": f"处理了输入: {input_str}，这是第 {counter} 次运行"}

# 创建工作流
workflow = Workflow(
    name="示例工作流",
    steps=my_workflow,
    db=SqliteDb(db_file="tmp/workflow.db"),
    session_id="my-session"
)

# 执行工作流
result = await workflow.arun(input="测试输入")
print(result.content)

# 获取会话状态
state = await workflow.aget_session_state()
print(f"计数器: {state.get('counter')}")

# 获取历史记录
history = await workflow.aget_chat_history(last_n_runs=3)
for interaction in history:
    print(f"输入: {interaction.input}, 输出: {interaction.output}")

# 获取指标
metrics = await workflow.aget_session_metrics()
if metrics:
    print(f"总 token: {metrics.total_tokens}, 总成本: {metrics.total_cost}")
```

---

## 注意事项

1. **数据库兼容性**: 
   - 同步方法需要同步数据库（`SqliteDb`）
   - 异步方法需要异步数据库（`PostgresDb` 或 `AsyncBaseDb` 子类）

2. **会话管理**: 
   - 会话状态在多次运行之间持久化
   - 使用 `session_state` 在步骤之间传递数据

3. **错误处理**: 
   - 所有方法都可能抛出异常，建议使用 try-except 包装

4. **性能**: 
   - 重用工作流实例，不要在循环中创建新实例
   - 使用缓存会话（`cache_session=True`）可以提高性能

5. **流式输出**: 
   - 流式输出时，确保正确处理事件迭代器
   - 在异步上下文中使用 `async for` 遍历事件

---

## 参考

- [Agno 官方文档](https://docs.agno.com)
- Workflow 类源代码: `agno/workflow/workflow.py`
- [Workflow 参数说明文档](./Workflow_参数说明.md)
- [Agno Agent 参数文档](./Agno_Agent_Agent_Parameters.md)
- [Agno Team 参数文档](./Agno_Team_Team_Parameters.md)

