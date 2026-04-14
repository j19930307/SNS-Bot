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

THREADS_ERROR_MARKERS = (
    "Not all who wander are lost, but this page is",
    "The link's not working or the page is gone",
)

THREADS_GRAPHQL_DOC_ID = "7448594591874178"
THREADS_GRAPHQL_LSD = "hgmSkqDnLNFckqa7t1vJdn"
THREADS_GRAPHQL_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "X-Fb-Lsd": THREADS_GRAPHQL_LSD,
    "X-Ig-App-Id": "238260118697367",
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


def _fetch_page_html(url: str) -> Tuple[str, str, int]:
    response = curl_requests.get(
        url,
        headers=DEFAULT_HEADERS,
        impersonate="chrome",
        timeout=30,
    )
    response.raise_for_status()
    return response.text, str(response.url), response.status_code


def _shortcode_to_post_id(post_code: str) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    post_id = 0
    normalized_code = post_code.split("?")[0].replace("/", "").strip()

    for letter in normalized_code:
        post_id = post_id * 64 + alphabet.index(letter)

    return str(post_id)


def _fetch_thread_items_from_graphql(post_code: str) -> Tuple[list, int]:
    variables = json.dumps(
        {
            "check_for_unavailable_replies": True,
            "first": 10,
            "postID": _shortcode_to_post_id(post_code),
            "__relay_internal__pv__BarcelonaIsLoggedInrelayprovider": True,
            "__relay_internal__pv__BarcelonaIsThreadContextHeaderEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsThreadContextHeaderFollowButtonEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaUseCometVideoPlaybackEnginerelayprovider": False,
            "__relay_internal__pv__BarcelonaOptionalCookiesEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsViewCountEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaShouldShowFediverseM075Featuresrelayprovider": False,
        },
        separators=(",", ":"),
    )
    response = curl_requests.post(
        "https://www.threads.com/api/graphql",
        headers=THREADS_GRAPHQL_HEADERS,
        data={
            "variables": variables,
            "doc_id": THREADS_GRAPHQL_DOC_ID,
            "lsd": THREADS_GRAPHQL_LSD,
        },
        impersonate="chrome",
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    errors = payload.get("errors") or []
    if errors:
        print(f"Threads GraphQL errors: {errors}")
        return [], response.status_code

    edges = jmespath.search("data.data.edges", payload) or []
    if not edges:
        return [], response.status_code

    thread_items = edges[0].get("node", {}).get("thread_items") or []
    return thread_items, response.status_code


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


def _extract_html_title(html: str) -> str:
    parser = HTMLParser(html)
    title_node = parser.css_first("title")
    return title_node.text(strip=True) if title_node else ""


def _is_threads_error_page(html: str) -> bool:
    return any(marker in html for marker in THREADS_ERROR_MARKERS)


def _log_response_diagnostics(
    *,
    requested_url: str,
    final_url: str,
    status_code: int,
    html: str,
) -> None:
    title = _extract_html_title(html)
    preview = re.sub(r"\s+", " ", html)[:200]
    is_error_page = _is_threads_error_page(html)
    print(
        "Threads response diagnostics: "
        f"requested_url={requested_url}, "
        f"final_url={final_url}, "
        f"status_code={status_code}, "
        f"title={title!r}, "
        f"is_error_page={is_error_page}, "
        f"html_preview={preview!r}"
    )


def _find_matching_post(
    thread_items: list,
    username: str,
    post_code: str,
) -> Optional[Dict[str, Any]]:
    return next(
        (
            parse_thread(thread["post"])
            for item in thread_items
            for thread in (item if isinstance(item, list) else [item])
            if thread["post"]["user"]["username"] == username
            and thread["post"]["code"] == post_code
        ),
        None,
    )


async def _try_graphql_fallback(username: str, post_code: str) -> Optional[Dict[str, Any]]:
    print("Trying Threads GraphQL fallback...")
    thread_items, status_code = await asyncio.to_thread(_fetch_thread_items_from_graphql, post_code)
    print(f"Threads GraphQL status_code={status_code}, thread_items={len(thread_items)}")

    if not thread_items:
        return None

    result = _find_matching_post(thread_items, username, post_code)
    if result:
        print("Threads GraphQL fallback parsed successfully")
    else:
        print("Threads GraphQL fallback did not find the target post")
    return result


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
            html, current_url, status_code = await asyncio.to_thread(_fetch_page_html, url)
            _log_response_diagnostics(
                requested_url=url,
                final_url=current_url,
                status_code=status_code,
                html=html,
            )
            thread_items = _extract_thread_items_from_html(html)

            if thread_items:
                result = _find_matching_post(thread_items, username, post_code)
                if result:
                    print("Threads post parsed successfully")
                    return result

                print("Matching Threads post not found in payload")
                graphql_result = await _try_graphql_fallback(username, post_code)
                if graphql_result:
                    return graphql_result
            else:
                print("No thread_items found in HTML payload")
                if _is_threads_error_page(html):
                    print("Threads returned a known error page marker")
                graphql_result = await _try_graphql_fallback(username, post_code)
                if graphql_result:
                    return graphql_result

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = f"threads_page_{timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as file:
                file.write(html)
            print(f"Saved debug HTML to {html_path}")
            error_code = "threads_error_page" if _is_threads_error_page(html) else "no_thread_items"
            return {
                "error": error_code,
                "url": current_url,
                "html_path": html_path,
                "status_code": status_code,
            }

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
