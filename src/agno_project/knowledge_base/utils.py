"""知识库工具函数。"""
import re
from typing import List, Dict, Any


def extract_images_from_text(text: str) -> List[str]:
    """
    从文本中提取图片链接。
    
    Args:
        text: 要处理的文本
        
    Returns:
        图片链接列表
    """
    images = []
    
    # Markdown图片格式: ![alt](url)
    markdown_pattern = r'!\[.*?\]\((.*?)\)'
    markdown_matches = re.findall(markdown_pattern, text)
    images.extend(markdown_matches)
    
    # HTML图片格式: <img src="url">
    html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    html_matches = re.findall(html_pattern, text, re.IGNORECASE)
    images.extend(html_matches)
    
    # 直接URL（以常见图片扩展名结尾）
    url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|bmp|webp|svg)'
    url_matches = re.findall(url_pattern, text, re.IGNORECASE)
    images.extend(url_matches)
    
    # 去重并返回
    return list(set(images))


def extract_structure_info(text: str) -> Dict[str, Any]:
    """
    从文本中提取结构信息。
    
    Args:
        text: 要处理的文本
        
    Returns:
        包含结构信息的字典
    """
    structure = {
        "has_code_block": False,
        "has_table": False,
        "has_list": False,
        "has_link": False,
        "heading_count": 0,
        "paragraph_count": 0
    }
    
    # 检查代码块
    if re.search(r'```', text):
        structure["has_code_block"] = True
    
    # 检查表格
    if re.search(r'\|.*\|', text):
        structure["has_table"] = True
    
    # 检查列表
    if re.search(r'^[\s]*[-*+]\s', text, re.MULTILINE) or re.search(r'^[\s]*\d+\.\s', text, re.MULTILINE):
        structure["has_list"] = True
    
    # 检查链接
    if re.search(r'\[.*?\]\(.*?\)', text) or re.search(r'https?://', text):
        structure["has_link"] = True
    
    # 统计标题数量
    heading_matches = re.findall(r'^#{1,6}\s+', text, re.MULTILINE)
    structure["heading_count"] = len(heading_matches)
    
    # 统计段落数量（简单估算：连续的非空行）
    paragraphs = re.split(r'\n\s*\n', text)
    structure["paragraph_count"] = len([p for p in paragraphs if p.strip()])
    
    return structure

