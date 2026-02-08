import asyncio
import json
import re
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs, unquote
import base64

import jmespath
from nested_lookup import nested_lookup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import aiohttp

from sns_info import SnsInfo, Profile


class MediaType(Enum):
    IMAGE = 1
    VIDEO = 2
    CAROUSEL_ALBUM = 8
    TEXT_POST = 19


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

    all_images, all_videos, all_attachments = extract_all_media(result)
    result["all_images"] = all_images
    result["all_videos"] = all_videos
    result["all_attachments"] = all_attachments
    result["url"] = f"https://www.threads.com/@{result['username']}/post/{result['code']}"

    print(result)
    return result


def extract_all_media(result):
    all_images = []
    all_videos = []
    all_attachments = []

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
            all_attachments.append(extract_original_url(result["attachment"]))

    return all_images, all_videos, all_attachments


def extract_original_url(threads_url: str) -> str:
    """從 Threads 的跳轉 URL 中提取原始 URL"""
    parsed_url = urlparse(threads_url)
    query_params = parse_qs(parsed_url.query)
    return unquote(query_params.get("u", [""])[0])


async def upload_to_imgur(image_path: str) -> Optional[str]:
    """
    上傳圖片到 Imgur

    Args:
        image_path: 圖片檔案路徑

    Returns:
        圖片 URL，失敗時返回 None
    """
    try:
        # Imgur 匿名上傳 API (無需註冊)
        # 這是 Imgur 的公開 Client ID，僅供匿名上傳使用
        client_id = "546c25a59c58ad7"

        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        headers = {
            'Authorization': f'Client-ID {client_id}'
        }

        data = {
            'image': image_data,
            'type': 'base64'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    'https://api.imgur.com/3/image',
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        image_url = result['data']['link']
                        print(f"☁️  圖片已上傳到 Imgur: {image_url}")
                        return image_url
                    else:
                        print(f"❌ Imgur 上傳失敗: {result}")
                else:
                    print(f"❌ Imgur 上傳失敗，狀態碼: {response.status}")

    except Exception as e:
        print(f"❌ 上傳圖片到 Imgur 時發生錯誤: {e}")

    return None


async def scrape_thread(url: str, max_retries: int = 1) -> dict:
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

    for attempt in range(max_retries):
        try:
            print(f"🔄 嘗試 {attempt + 1}/{max_retries}...")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # 使用快速載入，只等待 DOM 載入完成
                await page.goto(url, wait_until="domcontentloaded")

                scripts = await page.locator("script[type='application/json']").all()

                thread_items = []

                for i, script in enumerate(scripts):
                    content = await script.inner_text()

                    if '"ScheduledServerJS"' not in content or "thread_items" not in content:
                        continue

                    try:
                        data = json.loads(content)
                        thread_items.extend(nested_lookup("thread_items", data))
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
                        await browser.close()
                        return result
                    else:
                        print("⚠️  找不到匹配的貼文")
                        await browser.close()
                        # 不做截圖，直接返回空字典

                else:
                    print("⚠️  頁面中沒有找到 thread_items，擷取快照並上傳...")

                    # 只有在這個情況下才做完整的頁面載入和截圖
                    try:
                        # 等待頁面完全載入
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        await asyncio.sleep(2)

                        # 取得頁面標題和 URL 確認頁面有載入
                        page_title = await page.title()
                        current_url = page.url
                        print(f"📄 頁面標題: {page_title}")
                        print(f"🔗 當前 URL: {current_url}")

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = f"threads_screenshot_{timestamp}.png"
                        html_path = f"threads_page_{timestamp}.html"

                        # 儲存 HTML 內容
                        html_content = await page.content()
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        print(f"💾 HTML 已儲存: {html_path}")

                        # 截取完整頁面
                        await page.screenshot(path=screenshot_path, full_page=True)
                        print(f"📸 快照已儲存: {screenshot_path}")

                        # 上傳到 Imgur
                        imgur_url = await upload_to_imgur(screenshot_path)

                        await browser.close()

                        if imgur_url:
                            print(f"🔗 快照雲端連結: {imgur_url}")
                            # 將 URL 存入結果中，方便後續使用
                            return {"error": "no_thread_items", "screenshot_url": imgur_url, "url": url,
                                    "html_path": html_path}
                    except Exception as screenshot_error:
                        print(f"❌ 截圖過程發生錯誤: {screenshot_error}")
                        await browser.close()

            # 如果執行到這裡表示沒有返回資料，但也沒有錯誤，等待後重試
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⏳ 等待 {wait_time} 秒後重試...")
                await asyncio.sleep(wait_time)

        except PlaywrightTimeoutError as e:
            print(f"❌ 超時錯誤: {e}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                print(f"⏳ 等待 {wait_time} 秒後重試...")
                await asyncio.sleep(wait_time)

        except Exception as e:
            print(f"❌ 未預期的錯誤: {e}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⏳ 等待 {wait_time} 秒後重試...")
                await asyncio.sleep(wait_time)

    print(f"❌ 所有重試都失敗了")
    return {}


async def fetch_data_from_browser(url: str) -> Tuple[Optional[SnsInfo], Optional[SnsInfo]]:
    """
    從瀏覽器爬取資料並轉換為 SnsInfo

    Returns:
        (主貼文, 引用貼文) 的 tuple，失敗時返回 (None, None)
    """
    main_post = await scrape_thread(url)
    if not main_post:
        print("❌ 無法爬取主貼文")
        return None, None

    # 檢查是否有錯誤（只有 no_thread_items 錯誤會有 screenshot_url）
    if main_post.get("error"):
        print(f"❌ 爬取失敗，錯誤類型: {main_post['error']}")
        if main_post.get("screenshot_url"):
            print(f"📸 錯誤快照: {main_post['screenshot_url']}")
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
        attachments=(thread.get("all_attachments") or []),
        timestamp=datetime.fromtimestamp(thread["published_on"])
    )


if __name__ == "__main__":
    # 測試
    test_url = "https://www.threads.com/@cryforyysh/post/DQBQiuXjv-u"

    print("=" * 60)
    print("🚀 開始爬取 Threads 貼文")
    print("=" * 60)


    async def main():
        sns_info, share_info = await fetch_data_from_browser(test_url)

        if sns_info:
            print("\n✅ 主貼文:")
            print(sns_info)
        else:
            print("\n❌ 無法取得主貼文")

        if share_info:
            print("\n✅ 引用貼文:")
            print(share_info)


    asyncio.run(main())