import json
import re
from typing import Dict

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

from sns_info import SnsInfo, Profile


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
        post_video: post.video_versions[0].url
    }""",
        data,
    )

    result["all_images"] = []
    result["all_videos"] = []
    if result["attachment"]:
        result["all_videos"].append(result["attachment"])
    if result["carousel_images"]:
        result["all_images"].extend(result["carousel_images"])
    else:
        if result["post_image"] and not result["post_video"]:
            result["all_images"].append(result["post_image"])
    if result["carousel_videos"]:
        result["all_videos"].extend(result["carousel_videos"])
    else:
        if result["post_video"]:
            result["all_videos"].append(result["post_video"])

    if result["reply_count"] and isinstance(result["reply_count"], str):
        result["reply_count"] = int(result["reply_count"].split(" ")[0])

    result["url"] = f"https://www.threads.net/@{result['username']}/post/{result['code']}"

    return result


def scrape_thread(url: str) -> dict:
    match = re.search(r"@([^/]+)/post/", url)
    if match:
        username = match.group(1)
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
        driver.implicitly_wait(5)  # 等待網頁載入

        # 獲取網頁內容
        selector = Selector(driver.page_source)

        # 提取 JSON 數據
        hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()
        for hidden_dataset in hidden_datasets:
            if '"ScheduledServerJS"' not in hidden_dataset or "thread_items" not in hidden_dataset:
                continue
            data = json.loads(hidden_dataset)

            # 使用 nested_lookup 找出 thread_items
            thread_items = nested_lookup("thread_items", data)
            if not thread_items:
                continue

            # 解析 Threads 貼文
            threads = [parse_thread(t) for thread in thread_items for t in thread]

            # 找出指定用戶的主貼文
            thread = [thread for thread in threads if thread["username"] == username]
            if thread:
                return {
                    "thread": threads[0],  # 主貼文
                    "replies": threads[1:],  # 回覆
                }

        raise ValueError("Could not find thread data in page")
    finally:
        driver.quit()  # 關閉瀏覽器


def shorten_url(long_url):
    response = requests.get("https://tinyurl.com/api-create.php?url=" + long_url)
    return response.text


def fetch_data_from_browser(url: str):
    info = scrape_thread(url)
    print(info)
    thread = info["thread"]
    images = thread.get("all_images") or []
    videos = thread.get("all_videos") or []
    return SnsInfo(post_link=thread["url"],
                   profile=Profile(name=thread["username"], url=shorten_url(thread["user_pic"])),
                   content=thread["text"],
                   images=images,
                   videos=[shorten_url(video) for video in videos])


if __name__ == "__main__":
    print(fetch_data_from_browser("https://www.threads.net/@baggyubin73/post/DHhpcHmzlt5"))
