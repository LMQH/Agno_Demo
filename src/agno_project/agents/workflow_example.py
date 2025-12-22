"""工作流控制器使用示例。"""
import asyncio
from agno.db.mysql import MySQLDb

from .workflow_controller import WorkflowController
from ..config import get_config


async def main():
    """示例：使用工作流控制器处理用户问题。"""
    config = get_config()
    
    # 初始化数据库（可选）
    db = None
    if config.agent_db.enabled:
        from agno.db.mysql import MySQLDb
        db = MySQLDb(
            db_url=config.mysql.get_db_url(),
            schema=config.agent_db.db_schema or "ai"
        )
    
    # 创建工作流控制器
    controller = WorkflowController(db=db)
    
    # 处理用户问题
    question = "人工智能的发展对社会有什么影响？"
    result = await controller.process(
        question=question,
        session_id="test-session-001",
        user_id="test-user-001"
    )
    
    # 打印结果
    print(f"问题: {result['question']}")
    print(f"回答: {result['answer']}")
    print(f"来源数量: {result['num_sources']}")
    print(f"处理路径: {result['processing_path']}")
    
    if 'debate_result' in result:
        print(f"\n讨论结果: {result['debate_result'].get('summary', '')[:200]}...")
    
    if 'judgment_result' in result:
        print(f"\n判断结果: {result['judgment_result']}")


if __name__ == "__main__":
    asyncio.run(main())

