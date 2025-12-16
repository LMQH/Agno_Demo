#!/usr/bin/env python3
"""测试 Milvus 向量数据库连接。"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno_project.database.milvus_client import MilvusClient
from agno_project.config import get_config


def test_milvus_connection():
    """测试 Milvus 连接。"""
    print("=" * 50)
    print("Milvus 连接测试")
    print("=" * 50)
    
    try:
        # 获取配置
        config = get_config()
        print(f"连接信息: {config.milvus.host}:{config.milvus.port}")
        print(f"集合名称: {config.milvus.collection_name}")
        
        # 创建客户端
        print("\n1. 创建 Milvus 客户端...")
        client = MilvusClient()
        print("   [OK] 客户端创建成功")
        
        # 获取集合统计信息
        print("\n2. 获取集合统计信息...")
        stats = client.get_collection_stats()
        print(f"   [OK] 集合名称: {stats['collection_name']}")
        print(f"   [OK] 向量数量: {stats['num_entities']}")
        print(f"   [OK] 向量维度: {stats['dimension']}")
        
        # 测试搜索功能（即使集合为空也可以测试）
        print("\n3. 测试搜索功能...")
        # 创建一个测试向量（全零向量）
        test_vector = [[0.0] * stats['dimension']]
        try:
            results = client.search_vectors(
                query_embeddings=test_vector,
                top_k=1
            )
            print(f"   [OK] 搜索功能正常，返回 {len(results)} 个结果")
        except Exception as e:
            print(f"   [WARN] 搜索测试警告: {e}")
        
        # 关闭连接
        print("\n4. 关闭连接...")
        client.close()
        print("   [OK] 连接已关闭")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] Milvus 连接测试通过！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Milvus 连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return False


if __name__ == "__main__":
    success = test_milvus_connection()
    sys.exit(0 if success else 1)

