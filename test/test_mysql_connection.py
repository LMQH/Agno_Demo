#!/usr/bin/env python3
"""测试 MySQL 数据库连接。"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno_project.database.mysql_client import MySQLClient
from agno_project.config import get_config


def test_mysql_connection():
    """测试 MySQL 连接。"""
    print("=" * 50)
    print("MySQL 连接测试")
    print("=" * 50)
    
    try:
        # 获取配置
        config = get_config()
        print(f"连接信息: {config.mysql.host}:{config.mysql.port}/{config.mysql.database}")
        
        # 先测试服务器连接（不指定数据库）
        print("\n1. 测试 MySQL 服务器连接...")
        from sqlalchemy import create_engine, text  # type: ignore
        server_url = f"mysql+pymysql://{config.mysql.user}:{config.mysql.password}@{config.mysql.host}:{config.mysql.port}"
        server_engine = create_engine(server_url, pool_pre_ping=True)
        with server_engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("   [OK] MySQL 服务器连接成功")
        
        # 检查数据库是否存在
        print("\n2. 检查数据库是否存在...")
        with server_engine.connect() as conn:
            result = conn.execute(text("SHOW DATABASES"))
            databases = [row[0] for row in result.fetchall()]
            if config.mysql.database in databases:
                print(f"   [OK] 数据库 '{config.mysql.database}' 存在")
            else:
                print(f"   [WARN] 数据库 '{config.mysql.database}' 不存在")
                print(f"   可用数据库: {', '.join(databases[:5])}")
                print(f"   提示: 请先创建数据库或修改配置文件中的数据库名称")
                server_engine.dispose()
                print("\n" + "=" * 50)
                print("[PARTIAL] MySQL 服务器连接成功，但目标数据库不存在")
                print("=" * 50)
                return False
        
        # 创建客户端（指定数据库）
        print("\n3. 创建 MySQL 客户端（连接指定数据库）...")
        client = MySQLClient()
        print("   [OK] 客户端创建成功")
        
        # 测试连接
        print("\n4. 测试数据库连接...")
        with client.get_session() as session:
            result = session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("   [OK] 连接成功，可以执行查询")
        
        # 测试查询数据库版本
        print("\n5. 查询数据库版本...")
        version = client.execute_query("SELECT VERSION() as version")
        if version:
            print(f"   [OK] MySQL 版本: {version[0][0]}")
        
        # 检查表是否存在
        print("\n6. 检查表结构...")
        tables = client.execute_query("SHOW TABLES")
        if tables:
            print(f"   [OK] 数据库中有 {len(tables)} 个表")
            for table in tables[:5]:  # 只显示前5个
                print(f"     - {table[0]}")
        else:
            print("   [INFO] 数据库中暂无表")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] MySQL 连接测试通过！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] MySQL 连接测试失败: {e}")
        print("=" * 50)
        return False


if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)

