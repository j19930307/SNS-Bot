import asyncio
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from curl_cffi import requests as curl_requests
import jmespath
from nested_lookup import nested_lookup
from selectolax.parser import HTMLParser
from sns_core import PostAuthor, SocialPost


class MediaType(Enum):
    IMAGE = 1
    VIDEO = 2
    CAROUSEL_ALBUM = 8
    TEXT_POST = 19


DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "upgrade-insecure-requests": "1",
}


def parse_thread(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Threads post JSON dataset for the most important fields."""
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
        data,
    )

    all_images, all_videos, all_attachments = extract_all_media(result)
    result["all_images"] = all_images
    result["all_videos"] = all_videos
    result["all_attachments"] = all_attachments
    result["url"] = f"https://www.threads.com/@{result['username']}/post/{result['code']}"

    print(result)
    return result


def extract_all_media(result: Dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    all_images: list[str] = []
    all_videos: list[str] = []
    all_attachments: list[str] = []

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
    parsed_url = urlparse(threads_url)
    query_params = parse_qs(parsed_url.query)
    return unquote(query_params.get("u", [""])[0])


def _fetch_page_html(url: str) -> Tuple[str, str]:
    response = curl_requests.get(
        url,
        headers=DEFAULT_HEADERS,
        impersonate="chrome",
        timeout=30,
    )
    response.raise_for_status()
    return response.text, str(response.url)


def _extract_thread_items_from_html(html: str) -> list:
    parser = HTMLParser(html)
    thread_items = []

    for script in parser.css("script[type='application/json']"):
        content = script.text()
        if not content or '"ScheduledServerJS"' not in content or "thread_items" not in content:
            continue

        try:
            data = json.loads(content)
        except json.JSONDecodeError as error:
            print(f"JSON parse failed: {error}")
            continue

        thread_items.extend(nested_lookup("thread_items", data))

    return thread_items


def _find_matching_post(
    thread_items: list,
    username: str,
    post_code: str,
) -> Optional[Dict[str, Any]]:
    return next(
        (
            parse_thread(thread["post"])
            for item in thread_items
            for thread in item
            if thread["post"]["user"]["username"] == username
            and thread["post"]["code"] == post_code
        ),
        None,
    )


async def scrape_thread(url: str, max_retries: int = 1) -> dict:
    pattern = r"threads\.com/@([\w.]+)/post/([\w-]+)"
    match = re.search(pattern, url)
    if not match:
        print(f"Invalid Threads URL: {url}")
        return {}

    username, post_code = match.groups()

    for attempt in range(max_retries):
        try:
            print(f"Fetch attempt {attempt + 1}/{max_retries}...")
            html, current_url = await asyncio.to_thread(_fetch_page_html, url)
            thread_items = _extract_thread_items_from_html(html)

            if thread_items:
                result = _find_matching_post(thread_items, username, post_code)
                if result:
                    print("Threads post parsed successfully")
                    return result

                print("Matching Threads post not found in payload")
            else:
                print("No thread_items found in HTML payload")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = f"threads_page_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as file:
                file.write(html)
            print(f"Saved debug HTML to {html_path}")
            return {"error": "no_thread_items", "url": current_url, "html_path": html_path}

        except Exception as error:
            print(f"Threads fetch failed: {error}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"Retrying after {wait_time} seconds...")
                await asyncio.sleep(wait_time)

    print("Failed to fetch Threads post")
    return {}


async def fetch_data_from_browser(url: str) -> Tuple[Optional[SocialPost], Optional[SocialPost]]:
    main_post = await scrape_thread(url)
    if not main_post:
        print("Failed to fetch the main Threads post")
        return None, None

    if main_post.get("error"):
        print(f"Threads crawler error: {main_post['error']}")
        if main_post.get("html_path"):
            print(f"Debug HTML saved to: {main_post['html_path']}")
        return None, None

    quoted_post = None
    if main_post.get("share_info"):
        quoted = main_post["share_info"].get("quoted_post")
        if quoted and quoted.get("code"):
            try:
                quoted_post = convert_to_social_post(parse_thread(quoted))
            except Exception as error:
                print(f"Quoted post conversion failed: {error}")

    return convert_to_social_post(main_post), quoted_post


def convert_to_social_post(thread: Dict[str, Any]) -> SocialPost:
    return SocialPost(
        post_link=thread["url"],
        author=PostAuthor(name=thread["username"], url=thread["user_pic"]),
        text=thread["text"],
        images=(thread.get("all_images") or []),
        videos=(thread.get("all_videos") or []),
        links=(thread.get("all_attachments") or []),
        created_at=datetime.fromtimestamp(thread["published_on"]),
    )


if __name__ == "__main__":
    test_url = "https://www.threads.com/@cryforyysh/post/DQBQiuXjv-u"

    print("=" * 60)
    print("Testing Threads crawler")
    print("=" * 60)

    async def main():
        social_post, share_info = await fetch_data_from_browser(test_url)

        if social_post:
            print("\nMain post:")
            print(social_post)
        else:
            print("\nFailed to fetch main post")

        if share_info:
            print("\nQuoted post:")
            print(share_info)

    asyncio.run(main())