"""
URL 相關工具函數
"""
import re
from urllib.parse import urlparse, urlunparse

import requests


def extract_domain(url: str) -> str:
    """
    從 URL 中提取域名

    Args:
        url: 要解析的 URL

    Returns:
        域名字符串，如果無法解析則返回 None
    """
    match = re.search(r'https://(www\.)?([^/]+)', url)
    if match:
        return match.group(2)
    return None


def convert_to_custom_instagram_url(link: str) -> str:
    """
        將 Instagram 連結轉換為 zzinstagram
    """
    if link.startswith("https://www.instagram.com"):
        parsed_url = urlparse(link)
        # 修改 netloc 來將 'instagram.com' 替換為 'zzinstagram.com'
        modified_netloc = parsed_url.netloc.replace("instagram.com", "zzinstagram.com")
        # 使用已修改的 netloc 並移除 query 參數來重建 URL
        modified_url = urlunparse(
            (parsed_url.scheme, modified_netloc, parsed_url.path, parsed_url.params, '', parsed_url.fragment))
        return modified_url
    return link


def shorten_url(original_url: str) -> str:
    providers = [
        "https://is.gd/create.php",
        "https://v.gd/create.php"
    ]

    for endpoint in providers:
        try:
            response = requests.get(
                endpoint,
                params={
                    "format": "simple",
                    "url": original_url,
                },
                timeout=5,
            )
            if response.ok and response.text.startswith("http"):
                return response.text.strip()
        except Exception:
            continue

    # 全部失敗就回傳原始 URL
    return original_url
