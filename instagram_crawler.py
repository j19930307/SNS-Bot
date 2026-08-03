import json
import re
from datetime import datetime
from typing import Dict
from urllib.parse import quote

import httpx
import jmespath
import requests
from bs4 import BeautifulSoup
from sns_core import SocialPost, PostAuthor


def parse_post(data: Dict) -> Dict:
    print(f"parsing post data {data.get('shortcode')}")
    result = jmespath.search("""{
        id: id,
        shortcode: shortcode,
        src: display_url,
        video_url: video_url,
        taken_at: taken_at_timestamp,
        is_video: is_video,
        captions: edge_media_to_caption.edges[0].node.text,
        username: owner.username,
        full_name: owner.full_name,
        profile_pic_url: owner.profile_pic_url,
        videos_url: edge_sidecar_to_children.edges[?node.is_video==`true`].node.video_url,
        images_url: edge_sidecar_to_children.edges[?node.is_video==`false`].node.display_url
    }""", data)
    return result


def fetch_data_from_graphql(url):
    pattern = r"/(reel|reels|p)/([^/]+)/?"
    match = re.search(pattern, url)

    if not match:
        return None
    shortcode = match.group(2)
    response_dict = scrape_post_by_graphql(shortcode)
    if not response_dict:
        response_dict = scrape_post_by_embed(shortcode)
    if not response_dict:
        return None

    post_dict = parse_post(response_dict)
    images_url = []
    videos_url = []

    if post_dict.get("is_video"):
        video_url = post_dict.get("video_url")
        if video_url:
            videos_url.append(video_url)
        else:
            # Fallback to thumbnail display url if video_url is missing (e.g. copyright blocked)
            display_url = post_dict.get("src")
            if display_url:
                images_url.append(display_url)
    else:
        images_url = post_dict.get("images_url") or []
        videos_url = post_dict.get("videos_url") or []
        if not images_url and post_dict.get("src"):
            images_url.append(post_dict.get("src"))

    images_url = [u for u in images_url if u]
    videos_url = [u for u in videos_url if u]
        
    taken_at_timestamp = post_dict.get('taken_at')
    created_at = datetime.fromtimestamp(taken_at_timestamp) if taken_at_timestamp else None

    return SocialPost(post_link=url,
                      author=PostAuthor(name=f"{post_dict['username']}",
                                        url=post_dict['profile_pic_url']),
                      text=post_dict['captions'], images=images_url, videos=videos_url,
                      created_at=created_at)


def scrape_post_by_graphql(shortcode: str) -> Dict:
    print(f"scraping instagram post via graphql: {shortcode}")
    doc_id = "10015901848480474"
    url = f"https://www.instagram.com/graphql/query/?doc_id={doc_id}&variables={quote(json.dumps({'shortcode': shortcode}))}"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.instagram.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "X-Ig-App-Id": "936619743392459"
    }
    try:
        result = httpx.get(
            url=url,
            headers=headers,
            timeout=30.0
        )
        if result.status_code == 200:
            data = json.loads(result.content)
            data_dict = data.get("data", {})
            return data_dict.get("xdt_shortcode_media") or data_dict.get("shortcode_media")
    except Exception as e:
        print(f"scrape_post_by_graphql failed: {e}")
    return None


def scrape_post_by_embed(shortcode: str):
    url = f"https://www.instagram.com/p/{shortcode}/embed/captioned"
    result = requests.get(url)

    if result.status_code != 200:
        print(f"抓取失敗 status code: {result.status_code} 錯誤訊息: {result.content}")
        return None

    soup = BeautifulSoup(result.content, 'lxml')
    script_tag = soup.find('script', string=re.compile(r's.handle'))
    if script_tag is None:
        return None
    match = re.search(r's\.handle\((\{.*?})\);', script_tag.string, re.DOTALL)

    if match:
        json_str = match.group(1)
        data = json.loads(json_str)
        try:
            context_json = data["require"][1][3][0].get("contextJSON")
            if context_json:
                context_dict = json.loads(context_json)
                gql_data = context_dict["gql_data"]
                if gql_data:
                    return gql_data["shortcode_media"]
        except IndexError:
            return None


if __name__ == "__main__":
    print(fetch_data_from_graphql("https://www.instagram.com/reel/DbidTrgzTtZ/"))