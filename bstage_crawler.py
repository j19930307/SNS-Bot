import re
import json
import requests
import jmespath
from urllib.parse import urlparse
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from dateutil import parser
from fake_useragent import UserAgent

from sns_info import SnsInfo, Profile


def parse_post(data: Dict) -> Dict:
    """解析貼文資料"""
    return jmespath.search(
        """{
        author_name: author.nickname,
        author_image_url: author.avatarImgPath,
        content: description,
        images: images,
        video: video.hlsPath.path,
        video_thumbnail: video.thumbnailPaths[0].path,
        published_at: publishedAt
    }""",
        data
    )


def extract_url_components(url: str) -> tuple[str, str, str]:
    """從URL中提取藝人名稱、feed ID和平台類型"""
    parsed = urlparse(url)
    path = parsed.path
    hostname = parsed.netloc

    # Pattern 1: artist.mnetplus.world
    if "artist.mnetplus.world" in hostname:
        pattern = r'/main/stg/([^/]+)/story/feed/([^/]+)'
        match = re.search(pattern, path)
        if match:
            return match.group(1), match.group(2), "mnetplus"

    # Pattern 2: *.bstage.in
    elif "bstage.in" in hostname:
        artist = hostname.split('.bstage.in')[0]
        pattern = r'/story/feed/([^/]+)'
        match = re.search(pattern, path)
        if match:
            return artist, match.group(1), "bstage"

    raise ValueError(f"無法解析URL: {url}")


def fetch_data_from_bstage(artist: str, feed_id: str) -> Optional[SnsInfo]:
    """從bstage平台抓取資料"""
    ua = UserAgent()
    headers = {'user-agent': ua.random}

    try:
        response = requests.get(
            url=f"https://{artist}.bstage.in/svc/home/api/v1/home/star/feeds",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        for item in data.get("items", []):
            if item.get("typeId") == feed_id:
                post = parse_post(item)
                if not post:
                    continue

                images = []
                videos = []

                # 處理圖片
                if post.get("images"):
                    images.extend(post["images"])

                # 處理影片縮圖
                if post.get("video_thumbnail"):
                    thumbnail_url = f"https://image.static.bstage.in/cdn-cgi/image/metadata=none/{artist}{post['video_thumbnail']}"
                    images.append(thumbnail_url)

                # 處理影片
                if post.get("video"):
                    video_url = f"https://media.static.bstage.in/{artist}{post['video']}"
                    videos.append(video_url)

                return SnsInfo(
                    post_link=f"https://{artist}.bstage.in/story/feed/{feed_id}",
                    profile=Profile(
                        name=post.get("author_name", ""),
                        url=post.get("author_image_url", "")
                    ),
                    content=post.get("content", ""),
                    images=images,
                    videos=videos,
                    timestamp=parser.isoparse(post["published_at"]) if post.get("published_at") else datetime.now()
                )

        print(f"在bstage中找不到feed_id: {feed_id}")
        return None

    except requests.RequestException as e:
        print(f"請求bstage失敗: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失敗: {e}")
        return None


def fetch_data_from_mnet_plus(artist: str, feed_id: str) -> Optional[SnsInfo]:
    """從mnetplus平台抓取資料"""
    ua = UserAgent()
    headers = {'user-agent': ua.random}

    try:
        response = requests.get(
            url=f"https://artist.mnetplus.world/svc/stg/{artist}/home/api/v1/home/star/feeds",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        for item in data.get("items", []):
            if item.get("typeId") == feed_id:
                post = parse_post(item)
                if not post:
                    continue

                images = []
                videos = []

                # 處理圖片
                if post.get("images"):
                    images.extend(post["images"])

                # 處理影片縮圖
                if post.get("video_thumbnail"):
                    thumbnail_url = f"https://image.static.bstage.in/cdn-cgi/image/metadata=none/{artist}{post['video_thumbnail']}"
                    images.append(thumbnail_url)

                # 處理影片
                if post.get("video"):
                    video_url = f"https://media.static.bstage.in/{artist}{post['video']}"
                    videos.append(video_url)

                return SnsInfo(
                    post_link=f"https://artist.mnetplus.world/main/stg/{artist}/story/feed/{feed_id}",
                    profile=Profile(
                        name=post.get("author_name", ""),
                        url=post.get("author_image_url", "")
                    ),
                    content=post.get("content", ""),
                    images=images,
                    videos=videos,
                    timestamp=parser.isoparse(post["published_at"]) if post.get("published_at") else datetime.now()
                )

        print(f"在mnetplus中找不到feed_id: {feed_id}")
        return None

    except requests.RequestException as e:
        print(f"請求mnetplus失敗: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失敗: {e}")
        return None


def fetch_data(url: str) -> Optional[SnsInfo]:
    """主要函數：根據URL抓取資料"""
    try:
        artist, feed_id, platform = extract_url_components(url)

        if platform == "bstage":
            return fetch_data_from_bstage(artist, feed_id)
        elif platform == "mnetplus":
            return fetch_data_from_mnet_plus(artist, feed_id)
        else:
            print(f"不支援的平台: {platform}")
            return None

    except ValueError as e:
        print(f"URL解析錯誤: {e}")
        return None
    except Exception as e:
        print(f"未預期的錯誤: {e}")
        return None


if __name__ == "__main__":
    # 測試URLs
    test_urls = [
        "https://gyubin.bstage.in/story/feed/68496c26d1150c44a6199fbc",
        "https://artist.mnetplus.world/main/stg/rescene-official/story/feed/68708c8eb426f64485f5fa40"
    ]

    for url in test_urls:
        print(f"\n正在處理: {url}")
        print("-" * 80)

        result = fetch_data(url)
        if result:
            print(f"作者: {result.profile.name}")
            print(f"內容: {result.content}")
            print(f"圖片數量: {len(result.images)}")
            print(f"影片數量: {len(result.videos)}")
            print(f"發布時間: {result.timestamp}")
            print(f"貼文連結: {result.post_link}")
        else:
            print("無法取得資料")