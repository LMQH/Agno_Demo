#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用配置文件转换工具：将 config/*.toml 转换为 config/*.txt
用于在Linux环境中将TOML应用配置转换为可读的文本格式

注意：此工具与 generate_requirements.py 不同：
- 此工具：转换应用配置文件（config/*.toml -> config/*.txt）
- generate_requirements.py：转换Python依赖文件（pyproject.toml -> requirements.txt）
"""
import os
import sys
import json
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("错误: 无法导入tomllib或tomli库")
        print("请安装: pip install tomli")
        sys.exit(1)


def toml_to_txt(toml_path: Path, txt_path: Path = None) -> Path:
    """
    将TOML文件转换为TXT格式
    
    Args:
        toml_path: TOML文件路径
        txt_path: 输出TXT文件路径，如果为None则自动生成
    
    Returns:
        输出TXT文件路径
    """
    if txt_path is None:
        txt_path = toml_path.with_suffix('.txt')
    
    # 读取TOML文件
    with open(toml_path, "rb") as f:
        config_data = tomllib.load(f)
    
    # 转换为格式化的文本
    lines = []
    lines.append(f"# 配置文件: {toml_path.name}")
    lines.append(f"# 转换时间: {os.popen('date').read().strip()}")
    lines.append("=" * 80)
    lines.append("")
    
    # 递归格式化配置数据
    def format_section(data, prefix="", indent=0):
        """递归格式化配置节"""
        result = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.append(f"{indent_str}[{full_key}]")
                result.extend(format_section(value, full_key, indent + 1))
            elif isinstance(value, list):
                result.append(f"{indent_str}{key} = {json.dumps(value, ensure_ascii=False)}")
            else:
                # 转义特殊字符
                if isinstance(value, str):
                    value_str = f'"{value}"'
                else:
                    value_str = str(value)
                result.append(f"{indent_str}{key} = {value_str}")
        
        return result
    
    lines.extend(format_section(config_data))
    
    # 写入TXT文件
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return txt_path


def convert_all_configs(config_dir: Path = None):
    """转换config目录下的所有TOML文件"""
    if config_dir is None:
        # 获取项目根目录
        script_dir = Path(__file__).parent.absolute()
        config_dir = script_dir.parent / "config"
    
    if not config_dir.exists():
        print(f"错误: 配置目录不存在: {config_dir}")
        return
    
    print(f"正在转换配置文件目录: {config_dir}")
    
    toml_files = list(config_dir.glob("*.toml"))
    if not toml_files:
        print("未找到TOML配置文件")
        return
    
    for toml_file in toml_files:
        try:
            txt_file = toml_to_txt(toml_file)
            print(f"✓ {toml_file.name} -> {txt_file.name}")
        except Exception as e:
            print(f"✗ 转换失败 {toml_file.name}: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 转换指定的文件
        toml_path = Path(sys.argv[1])
        if not toml_path.exists():
            print(f"错误: 文件不存在: {toml_path}")
            sys.exit(1)
        
        txt_path = toml_to_txt(toml_path)
        print(f"转换完成: {txt_path}")
    else:
        # 转换所有配置文件
        convert_all_configs()

