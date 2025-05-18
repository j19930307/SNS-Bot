import json
import re
from datetime import datetime
from enum import Enum
from typing import Dict
from urllib.parse import urlparse, parse_qs, unquote

import jmespath
import requests
from fake_useragent import UserAgent
from parsel import Selector
from nested_lookup import nested_lookup
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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
        text: caption.text,
        published_on: taken_at,
        id: id,
        pk: pk,
        code: code,
        username: user.username,
        user_pic: user.profile_pic_url,
        user_pk: user.pk,
        user_id: user.id,
        carousel_media: carousel_media,
        attachment: text_post_app_info.link_preview_attachment.url,
        post_image: image_versions2.candidates[0].url,
        post_video: video_versions[0].url,
        media_type: media_type,
        linked_inline_media: text_post_app_info.linked_inline_media,
        share_info: text_post_app_info.share_info
    }""",
        data
    )

    all_images, all_videos = extract_all_media(result)
    result["all_images"] = all_images
    result["all_videos"] = all_videos
    result["url"] = f"https://www.threads.com/@{result['username']}/post/{result['code']}"

    print(result)
    return result


def extract_all_media(result):
    all_images = []
    all_videos = []

    media_type = result.get("media_type")

    if media_type == MediaType.IMAGE.value:  # 只包含一張圖片的貼文
        if result.get("post_image") and not result.get("post_video"):
            all_images.append(shorten_url(result["post_image"]))

    elif media_type == MediaType.VIDEO.value:  # 只包含一則影片的貼文
        if result.get("post_video"):
            all_videos.append(shorten_url(result["post_video"]))

    elif media_type == MediaType.CAROUSEL_ALBUM.value:  # 輪播相簿貼文 (包含圖片或影片)
        for media in result.get("carousel_media", []):
            if media.get("video_versions"):
                all_videos.append(shorten_url(media["video_versions"][0]["url"]))
            else:
                all_images.append(media["image_versions2"]["candidates"][0]["url"])
    elif media_type == MediaType.TEXT_POST.value:  # 只包含文字內容的貼文
        linked_inline_media = result.get("linked_inline_media")
        # 貼文內如果有連結此欄位可能會有值 (目前只發現 Instagram 連結會有)
        if linked_inline_media:
            linked_media_type = linked_inline_media.get("media_type")
            if linked_media_type == MediaType.VIDEO.value:  # 只有一則影片
                all_videos.append(shorten_url(linked_inline_media["video_versions"][0]["url"]))
            elif linked_media_type == MediaType.IMAGE.value:  # 只有一張圖片
                all_images.append(linked_inline_media["image_versions2"]["candidates"][0]["url"])
            elif linked_media_type == MediaType.CAROUSEL_ALBUM.value:  # 多個圖片或影片
                for media in linked_inline_media.get("carousel_media", []):
                    if media.get("video_versions"):
                        all_videos.append(shorten_url(media["video_versions"][0]["url"]))
                    else:
                        all_images.append(media["image_versions2"]["candidates"][0]["url"])
        # 沒有值則顯示原始連結
        elif result.get("attachment"):
            all_videos.append(extract_original_url(result["attachment"]))

    return all_images, all_videos


def extract_original_url(threads_url: str) -> str:
    """從 Threads 的跳轉 URL 中提取原始 URL"""
    parsed_url = urlparse(threads_url)
    query_params = parse_qs(parsed_url.query)
    return unquote(query_params.get("u", [""])[0])  # 取得 'u' 參數的值並解碼


def scrape_thread(url: str) -> dict:
    pattern = r"threads\.com/@([\w.]+)/post/([\w-]+)"
    match = re.search(pattern, url)
    if not match:
        return {}

    username, post_code = match.groups()

    ua = UserAgent()
    user_agent = ua.random

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'script[type="application/json"][data-sjs]'))
        )

        page_source = driver.page_source  # 提早抓取後關掉
    finally:
        driver.quit()

    selector = Selector(page_source)
    hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()

    thread_items = []

    for hidden_dataset in hidden_datasets:
        if '"ScheduledServerJS"' not in hidden_dataset or "thread_items" not in hidden_dataset:
            continue
        data = json.loads(hidden_dataset)

        temp_thread_items = nested_lookup("thread_items", data)
        thread_items.extend(temp_thread_items)

    if thread_items:
        return next((parse_thread(thread["post"]) for item in thread_items for thread in item
                     if thread["post"]["user"]["username"] == username and thread["post"]["code"] == post_code),
                    None)
    else:
        return {}


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


def fetch_data_from_browser(url: str):
    main_post = scrape_thread(url)
    if not main_post: return None
    print(main_post)
    quoted_post = None
    if main_post.get("share_info"):
        quoted = main_post["share_info"].get("quoted_post")
        if quoted and quoted.get("code"):
            quoted_post = convert_to_sns_info(parse_thread(quoted))
    return convert_to_sns_info(main_post), quoted_post


def convert_to_sns_info(thread):
    return SnsInfo(post_link=thread["url"],
                   profile=Profile(name=thread["username"], url=shorten_url(thread["user_pic"])),
                   content=thread["text"],
                   images=(thread.get("all_images") or []),
                   videos=(thread.get("all_videos") or []),
                   timestamp=datetime.fromtimestamp(thread["published_on"]))


if __name__ == "__main__":
    sns_info, share_info = fetch_data_from_browser("https://www.threads.com/@hao_bear/post/DJAw4SSzOZ_")
    print(sns_info)
    print(share_info)
