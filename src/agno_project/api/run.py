"""应用程序入口点。"""
import uvicorn
from pathlib import Path
from ..config import get_config

if __name__ == "__main__":
    config = get_config()
    
    # 如果启用 reload，必须使用导入字符串而不是直接传递 app 对象
    if config.debug:
        # 使用导入字符串以支持 reload 功能
        project_root = Path(__file__).parent.parent.parent.parent
        uvicorn.run(
            "agno_project.api.main:app",  # 导入字符串格式
            host=config.host,
            port=config.port,
            reload=True,
            reload_dirs=[str(project_root / "src")]  # 指定监控的目录
        )
    else:
        # 生产环境直接导入 app 对象
        from .main import app
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            reload=False
        )

