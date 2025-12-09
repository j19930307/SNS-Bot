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

def shorten_url(long_url):
    try:
        # 嘗試使用 is.gd
        response = requests.get("https://is.gd/create.php", params={"format": "simple", "url": long_url}, timeout=5)
        if response.ok and response.text.startswith("http"):
            return response.text
    except Exception:
        pass

    try:
        # 嘗試使用 CleanURI
        response = requests.post("https://cleanuri.com/api/v1/shorten", data={"url": long_url}, timeout=5)
        if response.ok:
            result = response.json()
            if "result_url" in result:
                return result["result_url"]
    except Exception:
        pass

    return None  # 如果全部失敗則回傳 None
