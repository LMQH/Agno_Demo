"""生成 requirements.txt 文件的辅助脚本。
从 pyproject.toml 提取依赖并生成 requirements.txt

注意：此工具与 convert_config_toml.py 不同：
- 此工具：转换Python依赖文件（pyproject.toml -> requirements.txt）
- convert_config_toml.py：转换应用配置文件（config/*.toml -> config/*.txt）
"""
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from pathlib import Path

# 获取项目根目录（scripts 的父目录）
project_root = Path(__file__).parent.parent

# 读取 pyproject.toml
pyproject_path = project_root / "pyproject.toml"
if not pyproject_path.exists():
    raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

with open(pyproject_path, "rb") as f:
    data = tomllib.load(f)

# 提取依赖
deps = data.get("project", {}).get("dependencies", [])

# 写入 requirements.txt（在项目根目录）
requirements_path = project_root / "requirements.txt"
with open(requirements_path, "w", encoding="utf-8") as f:
    for dep in deps:
        f.write(f"{dep}\n")

print(f"✓ Requirements.txt generated successfully at {requirements_path}")
print(f"  Found {len(deps)} dependencies")

