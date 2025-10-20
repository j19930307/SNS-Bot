import json
import re
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs, unquote
import time

import jmespath
from fake_useragent import UserAgent
from nested_lookup import nested_lookup
from parsel import Selector
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException

from sns_info import SnsInfo, Profile


class MediaType(Enum):
    IMAGE = 1
    VIDEO = 2
    CAROUSEL_ALBUM = 8
    TEXT_POST = 19


def get_chrome_options() -> ChromeOptions:
    """建立穩定的 Chrome 選項設定"""
    chrome_options = ChromeOptions()

    # 基本設定
    chrome_options.add_argument("--headless=new")  # 使用新版 headless 模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # 解決 Docker 中的 shared memory 問題

    # 效能優化
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-software-rasterizer")

    # 穩定性設定
    chrome_options.add_argument("--disable-crash-reporter")
    chrome_options.add_argument("--disable-in-process-stack-traces")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")

    # 記憶體管理
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-breakpad")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-renderer-backgrounding")

    # 視窗設定
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--mute-audio")

    # User Agent
    ua = UserAgent()
    chrome_options.add_argument(f"user-agent={ua.random}")

    # 頁面載入策略
    chrome_options.page_load_strategy = 'eager'  # 不等待所有資源載入完成

    # 實驗性選項
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 偏好設定
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # 不載入圖片以節省資源
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    return chrome_options


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

    if media_type == MediaType.IMAGE.value:
        if result.get("post_image") and not result.get("post_video"):
            all_images.append(result["post_image"])

    elif media_type == MediaType.VIDEO.value:
        if result.get("post_video"):
            all_videos.append(result["post_video"])

    elif media_type == MediaType.CAROUSEL_ALBUM.value:
        for media in result.get("carousel_media", []):
            if media.get("video_versions"):
                all_videos.append(media["video_versions"][0]["url"])
            else:
                all_images.append(media["image_versions2"]["candidates"][0]["url"])

    elif media_type == MediaType.TEXT_POST.value:
        linked_inline_media = result.get("linked_inline_media")
        if linked_inline_media:
            linked_media_type = linked_inline_media.get("media_type")
            if linked_media_type == MediaType.VIDEO.value:
                all_videos.append(linked_inline_media["video_versions"][0]["url"])
            elif linked_media_type == MediaType.IMAGE.value:
                all_images.append(linked_inline_media["image_versions2"]["candidates"][0]["url"])
            elif linked_media_type == MediaType.CAROUSEL_ALBUM.value:
                for media in linked_inline_media.get("carousel_media", []):
                    if media.get("video_versions"):
                        all_videos.append(media["video_versions"][0]["url"])
                    else:
                        all_images.append(media["image_versions2"]["candidates"][0]["url"])
        elif result.get("attachment"):
            all_videos.append(extract_original_url(result["attachment"]))

    return all_images, all_videos


def extract_original_url(threads_url: str) -> str:
    """從 Threads 的跳轉 URL 中提取原始 URL"""
    parsed_url = urlparse(threads_url)
    query_params = parse_qs(parsed_url.query)
    return unquote(query_params.get("u", [""])[0])


def scrape_thread(url: str, max_retries: int = 3) -> dict:
    """
    爬取 Threads 貼文資料，增加錯誤處理和重試機制

    Args:
        url: Threads 貼文 URL
        max_retries: 最大重試次數

    Returns:
        貼文資料字典，失敗時返回空字典
    """
    pattern = r"threads\.com/@([\w.]+)/post/([\w-]+)"
    match = re.search(pattern, url)
    if not match:
        print(f"❌ URL 格式錯誤: {url}")
        return {}

    username, post_code = match.groups()
    driver = None

    for attempt in range(max_retries):
        try:
            print(f"🔄 嘗試 {attempt + 1}/{max_retries}...")

            # 建立 WebDriver
            chrome_options = get_chrome_options()
            driver = webdriver.Chrome(options=chrome_options)

            # 設定超時
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)

            # 訪問頁面
            driver.get(url)

            # 等待關鍵元素載入
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'script[type="application/json"][data-sjs]')
                )
            )

            # 給頁面一點時間完成 JavaScript 執行
            time.sleep(2)

            # 提早抓取 page source
            page_source = driver.page_source

            # 立即關閉瀏覽器釋放資源
            driver.quit()
            driver = None

            # 解析資料
            selector = Selector(page_source)
            hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()

            thread_items = []
            for hidden_dataset in hidden_datasets:
                if '"ScheduledServerJS"' not in hidden_dataset or "thread_items" not in hidden_dataset:
                    continue

                try:
                    data = json.loads(hidden_dataset)
                    temp_thread_items = nested_lookup("thread_items", data)
                    thread_items.extend(temp_thread_items)
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON 解析錯誤: {e}")
                    continue

            if thread_items:
                result = next(
                    (parse_thread(thread["post"])
                     for item in thread_items
                     for thread in item
                     if thread["post"]["user"]["username"] == username
                     and thread["post"]["code"] == post_code),
                    None
                )

                if result:
                    print("✅ 成功爬取資料")
                    return result
                else:
                    print("⚠️  找不到匹配的貼文")

            else:
                print("⚠️  頁面中沒有找到 thread_items")

            # 如果執行到這裡表示沒有返回資料，但也沒有錯誤，等待後重試
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⏳ 等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)

        except TimeoutException as e:
            print(f"❌ 超時錯誤: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                print(f"⏳ 等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)

        except WebDriverException as e:
            print(f"❌ WebDriver 錯誤: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None

            # 這種錯誤通常是瀏覽器崩潰，需要較長的等待時間
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"⏳ WebDriver 錯誤，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)

        except Exception as e:
            print(f"❌ 未預期的錯誤: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⏳ 等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)

        finally:
            # 確保 driver 被關閉
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    print(f"❌ 所有重試都失敗了")
    return {}


def fetch_data_from_browser(url: str) -> Tuple[Optional[SnsInfo], Optional[SnsInfo]]:
    """
    從瀏覽器爬取資料並轉換為 SnsInfo

    Returns:
        (主貼文, 引用貼文) 的 tuple，失敗時返回 (None, None)
    """
    main_post = scrape_thread(url)
    if not main_post:
        print("❌ 無法爬取主貼文")
        return None, None

    quoted_post = None
    if main_post.get("share_info"):
        quoted = main_post["share_info"].get("quoted_post")
        if quoted and quoted.get("code"):
            try:
                quoted_post = convert_to_sns_info(parse_thread(quoted))
            except Exception as e:
                print(f"⚠️  處理引用貼文時發生錯誤: {e}")

    return convert_to_sns_info(main_post), quoted_post


def convert_to_sns_info(thread: Dict) -> SnsInfo:
    """將 thread 資料轉換為 SnsInfo 物件"""
    return SnsInfo(
        post_link=thread["url"],
        profile=Profile(name=thread["username"], url=thread["user_pic"]),
        content=thread["text"],
        images=(thread.get("all_images") or []),
        videos=(thread.get("all_videos") or []),
        timestamp=datetime.fromtimestamp(thread["published_on"])
    )


if __name__ == "__main__":
    # 測試
    test_url = "https://www.threads.com/@cryforyysh/post/DQBQiuXjv-u"

    print("=" * 60)
    print("🚀 開始爬取 Threads 貼文")
    print("=" * 60)

    sns_info, share_info = fetch_data_from_browser(test_url)

    if sns_info:
        print("\n✅ 主貼文:")
        print(sns_info)
    else:
        print("\n❌ 無法取得主貼文")

    if share_info:
        print("\n✅ 引用貼文:")
        print(share_info)