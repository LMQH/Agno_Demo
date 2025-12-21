# 多智能体系统框架说明

## 架构概述

本框架实现了基于 Agno 的多智能体系统，用于地缘政治领域的分析和讨论。

## 目录结构

```
agents/
├── planning/          # 规划智能体（Router Agent）
│   └── planner_agent.py
├── capability/        # 能力型智能体
│   └── rag_agent.py   # RAG Agent（保留现有功能）
├── debate/            # 讨论团队
│   ├── conservative_agent.py  # 保守派 Agent
│   ├── radical_agent.py       # 激进派 Agent
│   └── official_agent.py      # 官方叙事 Agent
├── judgment/          # 判断/反思智能体
│   └── judge_agent.py # Eval Agent
├── terminal/          # 最终输出智能体
│   └── reply_agent.py # Reply Agent
├── registry.py        # Agent 注册与发现
└── orchestrator.py    # 多智能体协调器
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

**职责**：知识库检索与问答
- 保留现有的 RAG 功能
- 用于简单问题的直接回答

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

### 基本使用

```python
from agno_project.agents.orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

result = await orchestrator.process(
    question="你的问题",
    session_id="session_123",
    user_id="user_123"
)
```

## 工作流程

1. **Router Agent** 分析问题，制定处理计划
2. 根据计划执行相应的处理路径：
   - 直接工具执行 → RAG Agent
   - 多智能体讨论 → 讨论团队 → Eval Agent → Reply Agent
   - 降级处理 → RAG Agent（应用限制）
   - 拒绝处理 → 直接返回拒绝原因
3. **Reply Agent** 生成最终回答

## 待完善功能

- [ ] PlanOutput 的完整解析逻辑
- [ ] Eval Agent 的响应解析
- [ ] 讨论中的 sources 提取
- [ ] 降级处理的具体限制实现
- [ ] 推理轨迹存储的完整实现

