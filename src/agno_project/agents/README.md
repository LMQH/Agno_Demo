# 多智能体系统框架说明

## 架构概述

本框架实现了基于 Agno 的多智能体系统，采用**外部 Workflow + 内部 Team** 的设计架构。

## 核心设计理念

- **外部 Workflow**：控制全流程的执行顺序和条件判断
- **内部 Team**：负责讨论部分的自主协调，由 Leader 控制节奏
- **判断智能体**：控制讨论的结束时机，决定是否回到 RAG 检索

## 流程说明

1. **Planning 智能体**：判断启用的智能体（是否需要 RAG，是否需要讨论团队）
2. **RAG 智能体**：调用工具进行检索召回，只返回 chunk 候选，不作回答
3. **讨论团队（Team）**：由 Team 定义，Leader 负责协调，队员（激进、保守、官方）进行辩论
4. **判断智能体**：评估讨论结果，控制讨论是否停止，是否回到 RAG 再检索
5. **整合输出智能体**：根据传入结果（query、chunks、讨论结果、判断意见）整合输出

## 目录结构

```
agents/
├── planning/          # 规划智能体（Router Agent）
│   └── planner_agent.py
├── capability/        # 能力型智能体
│   └── rag_agent.py   # RAG Agent（只返回 chunks）
├── debate/            # 讨论团队
│   ├── conservative_agent.py  # 保守派 Agent
│   ├── radical_agent.py       # 激进派 Agent
│   ├── official_agent.py      # 官方叙事 Agent
│   └── debate_team.py         # 讨论团队（Team）
├── judgment/          # 判断/反思智能体
│   └── judge_agent.py # 判断智能体（控制讨论结束）
├── terminal/          # 最终输出智能体
│   └── reply_agent.py # 整合输出智能体
├── workflow_controller.py  # 工作流控制器
└── registry.py        # Agent 注册与发现
```

## 核心 Agent

### 1. Router Agent (PlannerAgent)

**职责**：治理与分流中枢
- 判断问题复杂度
- 判断风险等级
- 决定处理路径

**处理路径**：
- `direct_tool`: 直接工具执行
- `multi_agent_debate`: 多智能体讨论
- `degraded_analysis`: 降级处理
- `reject`: 拒绝处理

### 2. RAG Agent (RAGAgent)

**职责**：知识库检索
- 调用工具进行检索召回
- **只返回 chunk 候选，不作回答**
- 为后续的讨论和整合提供参考资料

### 3. 讨论团队 Agent

- **ConservativeAgent**: 保守派立场
- **RadicalAgent**: 激进派立场
- **OfficialAgent**: 官方叙事立场

### 4. Eval Agent (JudgeAgent)

**职责**：系统反思者
- 评估讨论质量
- 检查系统性盲区
- 建议是否终止讨论

### 5. Reply Agent (ReplyAgent)

**职责**：裁决与整合者
- 整合多 Agent 结果
- 区分事实共识、立场分歧、不确定性
- 生成最终回答

## 使用方式

```python
from agno_project.agents import WorkflowController
from agno.db.mysql import MySQLDb

# 初始化工作流控制器
controller = WorkflowController(db=db)

# 处理用户问题
result = await controller.process(
    question="你的问题",
    session_id="session_123",
    user_id="user_123"
)

# 结果包含：
# - question: 原始问题
# - answer: 最终回答
# - sources: RAG 检索到的 chunks
# - processing_path: 处理路径
# - debate_result: 讨论结果（如果有）
# - judgment_result: 判断结果（如果有）
```

## 工作流程

1. **Planning 智能体**：分析问题，判断是否需要 RAG 和讨论团队
2. **RAG 智能体**（如果需要）：检索相关 chunks，只返回候选，不作回答
3. **讨论团队**（如果需要）：
   - 由 Team 内部协调，Leader 控制节奏
   - 队员（激进、保守、官方）进行辩论
   - 返回阶段性讨论结果
4. **判断智能体**：
   - 评估讨论结果是否满足需求
   - 判断是否还能产生新的建设性讨论成果
   - 决定是否回到 RAG 再检索
   - **控制讨论是否停止**
5. **整合输出智能体**：
   - 根据传入结果（query、chunks、讨论结果、判断意见）整合
   - 生成最终回答

## 架构优势

1. **清晰的职责分离**：Workflow 控制流程，Team 负责讨论
2. **灵活的流程控制**：判断智能体可以动态决定是否继续讨论或回到 RAG
3. **自主的团队协调**：Team 内部由 Leader 协调，不进行强控制
4. **可扩展性**：易于添加新的智能体或修改流程

## 核心组件说明

### WorkflowController

工作流控制器是整个系统的入口，使用 Agno 的 `Workflow` 来定义和执行完整的处理流程。

**主要功能**：
- 协调各个智能体的执行顺序
- 根据 Planning 智能体的决策选择处理路径
- 管理讨论循环（由判断智能体控制）
- 整合最终结果

### DebateTeam

讨论团队使用 Agno 的 `Team` 实现多智能体协作讨论。

**团队结构**：
- **Leader**：负责协调队员和控制讨论节奏
- **Conservative Agent**：保守派立场
- **Radical Agent**：激进派立场
- **Official Agent**：官方叙事立场

**工作方式**：
- Leader 协调各队员进行讨论
- 队员根据各自立场提出观点并回应质疑
- 返回整合的阶段性讨论结果

### JudgeAgent

判断智能体负责评估讨论质量并控制讨论流程。

**核心功能**：
- 评估讨论是否充分
- 检查是否存在系统性盲区
- 判断是否还能产生新的建设性讨论成果
- 决定是否回到 RAG 检索更多信息
- **控制讨论是否停止**

**判断动作**：
- `terminate`：终止讨论
- `continue`：继续讨论
- `request_rag`：请求 RAG 检索更多信息

### ReplyAgent

整合输出智能体负责生成最终回答。

**输入来源**：
- 用户提问（query）
- RAG 检索的 chunks（如果有）
- 讨论团队的讨论结果（如果有）
- 判断智能体的评审意见（如果有）

**输出格式**：
- 事实共识
- 立场分歧（分别列出各立场的核心观点）
- 不确定性与未来变量
- 参考来源

