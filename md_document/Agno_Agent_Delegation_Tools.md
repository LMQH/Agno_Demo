# Agno 委派工具机制说明文档

## 概述

委派工具机制（Delegation Tools）是指将一个 Agent 作为工具（Tool）提供给另一个 Agent 使用的机制。这使得 Agent 可以将任务委派给其他专门的 Agent 来处理，实现更复杂的多智能体协作模式。

## 为什么需要委派工具机制？

1. **任务分解**：主 Agent 可以将复杂任务分解并委派给专门的 Agent
2. **专业化**：不同 Agent 可以专注于不同的领域和任务
3. **动态协作**：Agent 可以根据需要动态选择调用哪个 Agent
4. **可扩展性**：可以轻松添加新的专业 Agent 而不修改主 Agent

## 实现方式

### 方式 1：将 Agent 包装为函数工具

在 Agno 框架中，`tools` 参数接受 `Callable` 类型，因此可以将 Agent 包装成函数：

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from typing import Optional

# 创建专门的 Agent
researcher_agent = Agent(
    name="Researcher",
    model=OpenAIChat(id="gpt-4o"),
    instructions="你是一个专业的研究助手，擅长信息检索和分析",
)

# 将 Agent 包装为工具函数
def research_tool(query: str) -> str:
    """
    研究工具：使用专业的研究 Agent 进行信息检索和分析
    
    Args:
        query: 研究查询
    
    Returns:
        研究结果
    """
    response = researcher_agent.run(query)
    return response.content

# 主 Agent 使用委派工具
main_agent = Agent(
    name="MainAgent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[research_tool],  # 将 Agent 作为工具使用
    instructions="你可以使用研究工具来获取信息",
)
```

### 方式 2：使用 Function 包装器

Agno 框架可能提供 `Function` 类来更好地包装 Agent：

```python
from agno.agent import Agent
from agno.function import Function  # 如果存在此模块

# 创建专门的 Agent
writer_agent = Agent(
    name="Writer",
    model=OpenAIChat(id="gpt-4o"),
    instructions="你是一个专业的写作助手",
)

# 将 Agent 转换为 Function
def write_article(topic: str, style: str = "professional") -> str:
    """写作工具：使用专业的写作 Agent 生成文章"""
    prompt = f"请以{style}风格写一篇关于{topic}的文章"
    response = writer_agent.run(prompt)
    return response.content

# 主 Agent 使用
main_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[write_article],
    instructions="你可以使用写作工具来生成文章",
)
```

### 方式 3：异步委派

对于异步场景，可以使用异步函数：

```python
async def async_research_tool(query: str) -> str:
    """异步研究工具"""
    response = await researcher_agent.arun(query)
    return response.content

main_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[async_research_tool],
)
```

## 与 Team 模式的区别

### 委派工具机制（Delegation Tools）
- **控制方式**：主 Agent 主动选择何时调用哪个工具 Agent
- **使用场景**：主 Agent 需要特定功能时调用
- **灵活性**：主 Agent 可以决定是否使用、何时使用
- **示例**：主 Agent 需要研究时调用研究 Agent

### Team 模式
- **控制方式**：Team 协调器自动决定任务分配
- **使用场景**：需要多个 Agent 协作完成复杂任务
- **灵活性**：Team 协调器决定成员之间的交互
- **示例**：研究 + 分析 + 写作的协作流程

## 最佳实践

### 1. Agent 重用
**重要**：不要在工具函数中每次创建新的 Agent，应该重用已创建的 Agent：

```python
# ❌ 错误：每次调用都创建新 Agent
def research_tool(query: str) -> str:
    agent = Agent(...)  # 不要这样做！
    return agent.run(query).content

# ✅ 正确：重用已创建的 Agent
researcher_agent = Agent(...)  # 在模块级别创建

def research_tool(query: str) -> str:
    return researcher_agent.run(query).content
```

### 2. 清晰的工具描述
为工具函数提供清晰的文档字符串，帮助主 Agent 理解何时使用：

```python
def research_tool(query: str) -> str:
    """
    研究工具：使用专业的研究 Agent 进行信息检索和分析。
    
    适用于：
    - 需要查找最新信息
    - 需要分析复杂主题
    - 需要多角度研究
    
    参数:
        query: 研究查询，应明确具体
    
    返回:
        研究结果，包含关键信息和来源
    """
    return researcher_agent.run(query).content
```

### 3. 错误处理
在工具函数中添加错误处理：

```python
def research_tool(query: str) -> str:
    """研究工具"""
    try:
        response = researcher_agent.run(query)
        return response.content
    except Exception as e:
        return f"研究工具调用失败: {str(e)}"
```

### 4. 结构化输出
如果委派的 Agent 使用 `output_schema`，工具函数应该返回结构化数据：

```python
from pydantic import BaseModel

class ResearchResult(BaseModel):
    summary: str
    sources: list[str]
    key_points: list[str]

researcher_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    output_schema=ResearchResult,
    instructions="进行研究并返回结构化结果",
)

def research_tool(query: str) -> ResearchResult:
    """研究工具，返回结构化结果"""
    response = researcher_agent.run(query)
    return response.content  # 已经是 ResearchResult 类型
```

## 使用示例

### 示例 1：多专业 Agent 协作

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# 创建专业 Agent
researcher = Agent(
    name="Researcher",
    model=OpenAIChat(id="gpt-4o"),
    instructions="专业的研究助手",
)

writer = Agent(
    name="Writer",
    model=OpenAIChat(id="gpt-4o"),
    instructions="专业的写作助手",
)

editor = Agent(
    name="Editor",
    model=OpenAIChat(id="gpt-4o"),
    instructions="专业的编辑助手",
)

# 包装为工具
def research(query: str) -> str:
    return researcher.run(query).content

def write(topic: str, style: str = "professional") -> str:
    prompt = f"以{style}风格写关于{topic}的文章"
    return writer.run(prompt).content

def edit(text: str, focus: str = "clarity") -> str:
    prompt = f"编辑以下文本，重点关注{focus}：\n{text}"
    return editor.run(prompt).content

# 主 Agent 使用所有工具
main_agent = Agent(
    name="ContentManager",
    model=OpenAIChat(id="gpt-4o"),
    tools=[research, write, edit],
    instructions="""
    你是一个内容管理器，可以：
    1. 使用 research 工具进行研究
    2. 使用 write 工具进行写作
    3. 使用 edit 工具进行编辑
    
    根据任务需要选择合适的工具。
    """,
)
```

### 示例 2：条件委派

```python
def smart_research(query: str, depth: str = "standard") -> str:
    """
    智能研究工具：根据深度选择不同的研究策略
    
    参数:
        query: 研究查询
        depth: 研究深度 ("quick", "standard", "deep")
    """
    if depth == "quick":
        # 使用快速研究 Agent
        return quick_researcher.run(query).content
    elif depth == "deep":
        # 使用深度研究 Agent
        return deep_researcher.run(query).content
    else:
        # 使用标准研究 Agent
        return researcher.run(query).content
```

## 注意事项

1. **性能考虑**：委派工具会增加调用链的深度，可能影响响应时间
2. **成本控制**：每个委派调用都会产生 API 调用成本
3. **错误传播**：确保工具函数有适当的错误处理
4. **上下文传递**：考虑是否需要将主 Agent 的上下文传递给委派的 Agent
5. **会话管理**：委派的 Agent 可以使用独立的会话，也可以共享会话

## 与 Workflow 的对比

| 特性 | 委派工具机制 | Workflow |
|------|------------|----------|
| 控制方式 | Agent 自主决定 | 程序化控制 |
| 灵活性 | 动态选择 | 固定流程 |
| 适用场景 | 需要智能选择 | 需要明确步骤 |
| 复杂度 | 中等 | 可高可低 |

## 总结

委派工具机制是 Agno 框架中实现多智能体协作的重要方式之一。虽然当前文档中没有明确说明，但通过将 Agent 包装为函数工具，可以实现灵活的委派模式。这种方式特别适合需要主 Agent 根据情况动态选择调用哪个专业 Agent 的场景。

## 参考

- [Agno Agent 参数文档](./Agno_Agent_Agent_Parameters.md)
- [Agno Team 参数文档](./Agno_Team_Team_Parameters.md)
- [Agno Workflow 参数文档](./Agno_Workflow_Workflow_Parameters.md)
- [Agno 官方文档](https://docs.agno.com)

