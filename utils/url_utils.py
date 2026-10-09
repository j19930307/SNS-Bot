"""URL 工具模組
提供短網址轉換等功能。
"""
import requests


def shorten_url(original_url: str) -> str:
    """將長網址縮短，提供 da.gd -> TinyURL -> spoo.me 多重容錯機制。

    若所有服務皆無法使用，則退回原網址。
    """
    # 1. 首選：da.gd（純 302 跳轉、無 noindex 標籤，對 Discord 預覽相容性最佳）
    try:
        response = requests.get(
            "https://da.gd/s",
            params={"url": original_url},
            timeout=5,
        )
        if response.ok and response.text.startswith("http"):
            return response.text.strip()
    except Exception:
        pass

    # 2. 備用 1：TinyURL（穩定老牌）
    try:
        response = requests.get(
            "https://tinyurl.com/api-create.php",
            params={"url": original_url},
            timeout=5,
        )
        if response.ok and response.text.startswith("http"):
            return response.text.strip()
    except Exception:
        pass

    # 3. 備用 2：spoo.me（無廣告、JSON API）
    try:
        response = requests.post(
            "https://spoo.me",
            data={"url": original_url},
            headers={"Accept": "application/json"},
            timeout=5,
        )
        if response.ok:
            data = response.json()
            short_url = data.get("short_url")
            if short_url and short_url.startswith("http"):
                return short_url
    except Exception:
        pass

    return original_url
