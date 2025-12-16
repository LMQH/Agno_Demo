"""应用程序的主入口点。"""
import sys
from pathlib import Path

# 将 src 添加到路径
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import uvicorn
from agno_project.config import get_config

if __name__ == "__main__":
    # 启动时生成 requirements.txt
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            
            dependencies = data.get("project", {}).get("dependencies", [])
            
            requirements_path = project_root / "requirements.txt"
            with open(requirements_path, "w", encoding="utf-8") as f:
                for dep in dependencies:
                    f.write(f"{dep}\n")
    except Exception as e:
        print(f"Warning: Failed to generate requirements.txt: {e}")
    
    # 获取配置并启动服务器
    config = get_config()
    project_root = Path(__file__).parent.parent.parent
    
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
        from agno_project.api.main import app
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            reload=False
        )

