import json
import re
from datetime import datetime
from enum import Enum
from itertools import chain
from typing import Dict
from urllib.parse import urlparse, parse_qs, unquote

import jmespath
import requests
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from parsel import Selector
from nested_lookup import nested_lookup
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By

from instagram_crawler import shorten_url
from sns_info import SnsInfo, Profile


class MediaType(Enum):
    IMAGE = 1  # 只包含一張圖片的貼文
    VIDEO = 2  # 只包含一則影片的貼文
    CAROUSEL_ALBUM = 8  # 輪播相簿貼文(包含圖片或影片)
    TEXT_POST = 19  # 只包含文字內容的貼文


def parse_thread(data: Dict) -> Dict:
    """Parse Threads post JSON dataset for the most important fields"""
    result = jmespath.search(
        """{
        text: post.caption.text,
        published_on: post.taken_at,
        id: post.id,
        pk: post.pk,
        code: post.code,
        username: post.user.username,
        user_pic: post.user.profile_pic_url,
        user_verified: post.user.is_verified,
        user_pk: post.user.pk,
        user_id: post.user.id,
        has_audio: post.has_audio,
        reply_count: view_replies_cta_string,
        like_count: post.like_count,
        carousel_images: post.carousel_media[?video_versions==null].image_versions2.candidates[0].url,
        image_count: post.carousel_media_count,
        carousel_videos: post.carousel_media[?video_versions].video_versions[0].url,
        attachment: post.text_post_app_info.link_preview_attachment.url
        post_image: post.image_versions2.candidates[0].url
        post_video: post.video_versions[0].url,
        media_type: post.media_type,
        linked_inline_media: post.text_post_app_info.linked_inline_media
    }""",
        data
    )

    result["all_images"] = []
    result["all_videos"] = []

    if result["media_type"] == MediaType.IMAGE.value:  # 只包含一張圖片的貼文
        if result["post_image"] and not result["post_video"]:
            result["all_images"].append(shorten_url(result["post_image"]))
    elif result["media_type"] == MediaType.VIDEO.value:  # 只包含一則影片的貼文
        if result["post_video"]:
            result["all_videos"].append(shorten_url(result["post_video"]))
    elif result["media_type"] == MediaType.CAROUSEL_ALBUM.value:  # 輪播相簿貼文(包含圖片或影片)
        if result["carousel_images"]:
            result["all_images"].extend([img for img in result["carousel_images"]])
        if result["carousel_videos"]:
            result["all_videos"].extend([shorten_url(video) for video in result["carousel_videos"]])
    elif result["media_type"] == MediaType.TEXT_POST.value:  # 只包含文字內容的貼文
        linked_inline_media = result["linked_inline_media"]
        # 貼文內如果有連結此欄位可能會有值 (目前只發現 Instagram 連結會有)
        if linked_inline_media:
            if linked_inline_media["media_type"] == MediaType.VIDEO.value:  # 只有一張圖片
                result["all_videos"].append(shorten_url(linked_inline_media["video_versions"][0]["url"]))
            elif linked_inline_media["media_type"] == MediaType.IMAGE.value:  # 只有一則影片
                result["all_images"].append(linked_inline_media["image_versions2"]["candidates"][0]["url"])
            elif linked_inline_media["media_type"] == MediaType.CAROUSEL_ALBUM.value:  # 多個圖片或影片
                result["all_videos"].extend(
                    [shorten_url(media["video_versions"][0]["url"]) for media in linked_inline_media["carousel_media"]
                     if
                     media.get("video_versions")])
                result["all_images"].extend([media["image_versions2"]["candidates"][0]["url"] for media in
                                             linked_inline_media["carousel_media"] if not media.get("video_versions")])
        # 沒有值則顯示原始連結
        elif result["attachment"]:
            result["all_videos"].append(extract_original_url(result["attachment"]))

    if result["reply_count"] and isinstance(result["reply_count"], str):
        result["reply_count"] = int(result["reply_count"].split(" ")[0])

    result["url"] = f"https://www.threads.net/@{result['username']}/post/{result['code']}"

    print(result)
    return result


def extract_original_url(threads_url: str) -> str:
    """從 Threads 的跳轉 URL 中提取原始 URL"""
    parsed_url = urlparse(threads_url)
    query_params = parse_qs(parsed_url.query)
    return unquote(query_params.get("u", [""])[0])  # 取得 'u' 參數的值並解碼


def scrape_thread(url: str) -> dict:
    pattern = r"threads\.net/@([\w.]+)/post/([\w-]+)"
    match = re.search(pattern, url)
    if match:
        username, post_code = match.groups()
    else:
        return {}

    """Scrape Threads post and replies using Selenium"""
    ua = UserAgent()
    user_agent = ua.random

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")  # 啟用無頭模式
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 避免被偵測
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f'user-agent={user_agent}')

    # options = ChromeOptions()
    # options.add_argument("--start-maximized")
    # options.add_argument('--headless')
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # 啟動 ChromeDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        driver.implicitly_wait(10)  # 等待網頁載入

        # 獲取網頁內容
        selector = Selector(driver.page_source)

        # 提取 JSON 數據
        hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()

        thread_items = []

        for hidden_dataset in hidden_datasets:
            if '"ScheduledServerJS"' not in hidden_dataset or "thread_items" not in hidden_dataset:
                continue
            data = json.loads(hidden_dataset)

            # 使用 nested_lookup 找出 thread_items
            temp_thread_items = nested_lookup("thread_items", data)
            thread_items.extend(temp_thread_items)

        if thread_items:
            # 找出指定用戶的主貼文
            return next((parse_thread(thread) for item in thread_items for thread in item
                         if thread["post"]["user"]["username"] == username and thread["post"]["code"] == post_code),
                        None)
        else:
            return {}
    finally:
        driver.quit()  # 關閉瀏覽器


def shorten_url(long_url):
    response = requests.get("https://tinyurl.com/api-create.php?url=" + long_url)
    return response.text


def fetch_data_from_browser(url: str):
    thread = scrape_thread(url)
    if not thread: return
    print(thread)
    images = thread.get("all_images") or []
    videos = thread.get("all_videos") or []
    return SnsInfo(post_link=thread["url"],
                   profile=Profile(name=thread["username"], url=shorten_url(thread["user_pic"])),
                   content=thread["text"],
                   images=images,
                   videos=videos,
                   timestamp=datetime.fromtimestamp(thread["published_on"]))


if __name__ == "__main__":
    print(fetch_data_from_browser("https://www.threads.net/@jiawen_516/post/C7RTaLPvHCQ/?xmt=AQGzSKH2pbap4CBbulL5kXEwW8AafDdViGPVRr8vKwL4zw"))
