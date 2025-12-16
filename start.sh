#!/bin/bash

# Agno RAG System Startup Script
# Supports Linux deployment
# 根据IP地址自动选择配置文件并启动应用

set -e

echo "============================================================"
echo "Agno RAG System - Linux 启动脚本"
echo "============================================================"

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 生成 requirements.txt
echo ""
echo "生成 requirements.txt..."
if command -v pip-compile &> /dev/null; then
    pip-compile pyproject.toml -o requirements.txt
    echo "✓ requirements.txt 生成成功（使用 pip-compile）"
else
    # 使用项目脚本生成
    if [ -f "scripts/generate_requirements.py" ]; then
        python3 scripts/generate_requirements.py
    else
        # 回退方案：从 pyproject.toml 提取依赖
        python3 << 'EOF'
try:
    import tomllib
except ImportError:
    import tomli as tomllib

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)

deps = data.get("project", {}).get("dependencies", [])
with open("requirements.txt", "w") as f:
    for dep in deps:
        f.write(f"{dep}\n")
print("✓ requirements.txt 生成成功（回退方案）")
EOF
    fi
fi

# 安装依赖（如果需要）
if [ "$INSTALL_DEPS" = "true" ]; then
    echo ""
    echo "安装依赖..."
    pip install -r requirements.txt
fi

# 以可编辑模式安装包
echo ""
echo "以可编辑模式安装包..."
pip install -e . > /dev/null 2>&1

# 转换TOML配置文件为TXT格式（用于某些不支持TOML的环境）
echo ""
echo "转换TOML配置文件为TXT格式..."
if [ -f "scripts/convert_config_toml.py" ]; then
    python3 scripts/convert_config_toml.py
    echo "✓ 配置文件转换完成"
else
    echo "⚠ 警告: 未找到 convert_config_toml.py 脚本，跳过转换"
fi

# 检测IP地址并自动选择环境
echo ""
echo "检测IP地址并选择环境..."
python3 << EOF
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path("$SCRIPT_DIR")
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from agno_project.config import detect_environment, get_local_ip
    
    ip = get_local_ip()
    env = detect_environment()
    
    print(f"检测到的IP地址: {ip}")
    print(f"自动选择的环境: {env}")
    
    # 设置环境变量（通过文件传递，因为子进程无法直接修改父进程环境）
    with open("/tmp/agno_env.txt", "w") as f:
        f.write(env)
    print(f"环境已保存: {env}")
except Exception as e:
    print(f"警告: 配置检测失败: {e}")
    print("将使用默认环境变量或开发环境")
    with open("/tmp/agno_env.txt", "w") as f:
        f.write("dev")
EOF

# 读取Python脚本设置的环境
if [ -f "/tmp/agno_env.txt" ]; then
    ENVIRONMENT=$(cat /tmp/agno_env.txt)
    rm -f /tmp/agno_env.txt
else
    ENVIRONMENT=${ENVIRONMENT:-dev}
fi
export ENVIRONMENT

echo ""
echo "============================================================"
echo "启动 FastAPI 服务器..."
echo "环境: $ENVIRONMENT"
echo "============================================================"
echo ""

# 启动应用
python3 -m uvicorn agno_project.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload

