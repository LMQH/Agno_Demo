#!/usr/bin/env python3
"""交互式 CLI 应用，用于测试与 Debate Team 的直接交互。

参照官方示例创建，使用 Team.cli_app() 方法提供交互式命令行界面。
"""
import sys
from pathlib import Path
from typing import Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.db.sqlite import SqliteDb
from agno_project.agents.debate.debate_team import DebateTeam


def create_db_connection() -> Optional[SqliteDb]:
    """创建 SQLite 数据库连接。"""
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        sqlite_dir = project_root / "data" / "sqlite"
        
        # 确保 sqlite 文件夹存在
        sqlite_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建数据库文件路径
        db_file = sqlite_dir / "debate_team.db"
        
        # 创建 SQLite 数据库连接
        db = SqliteDb(db_file=str(db_file))
        print(f"✓ SQLite 数据库连接成功: {db_file}")
        return db
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("将使用无数据库模式运行（无会话持久化）")
        return None


def main():
    """主函数。"""
    print("=" * 60)
    print("Agno Debate Team - 交互式 CLI")
    print("=" * 60)
    print()
    
    # 创建数据库连接
    db = create_db_connection()
    
    # 初始化 DebateTeam
    try:
        debate_team = DebateTeam(db=db)
        print("✓ DebateTeam 初始化成功")
        print(f"  - 团队成员: Leader, Conservative, Radical, Official")
    except Exception as e:
        print(f"✗ DebateTeam 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("开始交互式会话（输入 'quit' 或 'exit' 退出）")
    print("=" * 60)
    print("提示: 团队将进行多立场讨论，最终返回讨论结果")
    print()
    
    # 使用 Team 的 cli_app 方法
    try:
        debate_team.team.cli_app(stream=True)
    except KeyboardInterrupt:
        print("\n\n再见！")
    except Exception as e:
        print(f"\n程序异常退出: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
