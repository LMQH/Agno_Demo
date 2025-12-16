#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows 启动脚本
根据IP地址自动选择配置文件并启动应用
"""
import os
import sys
import platform
from pathlib import Path

# 将项目根目录添加到路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 将 src 添加到路径
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def main():
    """主启动函数"""
    print("=" * 60)
    print("Agno RAG System - Windows 启动脚本")
    print("=" * 60)
    
    # 显示系统信息
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    print(f"项目根目录: {project_root}")
    print()
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"虚拟环境: {sys.prefix}")
    else:
        print("虚拟环境: 未激活")
    print()
    
    # 导入配置检测函数
    try:
        from agno_project.config import detect_environment, get_local_ip
        
        # 显示IP和环境信息
        ip = get_local_ip()
        env = detect_environment()
        print(f"检测到的IP地址: {ip}")
        print(f"自动选择的环境: {env}")
        print()
        
        # 设置环境变量（可选，用于覆盖自动检测）
        if "ENVIRONMENT" not in os.environ:
            os.environ["ENVIRONMENT"] = env
            print(f"设置环境变量 ENVIRONMENT={env}")
        else:
            print(f"使用环境变量 ENVIRONMENT={os.environ['ENVIRONMENT']}")
        print()
        
    except Exception as e:
        print(f"警告: 配置检测失败: {e}")
        print("将使用默认环境变量或开发环境")
        print()
    
    # 启动应用
    print("正在启动 FastAPI 服务器...")
    print("-" * 60)
    
    try:
        from agno_project.config import get_config
        import uvicorn
        
        config = get_config()
        
        print(f"服务器地址: http://{config.host}:{config.port}")
        print(f"调试模式: {config.debug}")
        print(f"环境: {config.environment}")
        print("-" * 60)
        print()
        
        # 如果启用 reload，必须使用导入字符串而不是直接传递 app 对象
        if config.debug:
            # 使用导入字符串以支持 reload 功能
            uvicorn.run(
                "agno_project.api.main:app",  # 导入字符串格式
                host=config.host,
                port=config.port,
                reload=True,
                reload_dirs=[str(project_root / "src")]  # 指定监控的目录
            )
        else:
            # 生产环境直接导入 app 对象
            from agno_project.api.run import app
            uvicorn.run(
                app,
                host=config.host,
                port=config.port,
                reload=False
            )
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

