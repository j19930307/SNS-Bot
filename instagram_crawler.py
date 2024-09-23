import re
from datetime import datetime
import requests
import jmespath
from fake_useragent import UserAgent
from sns_info import SnsInfo, Profile
import json
from typing import Dict
from urllib.parse import quote
import httpx

INSTAGRAM_APP_ID = "936619743392459"


def shorten_url(long_url):
    response = requests.get("https://tinyurl.com/api-create.php?url=" + long_url)
    return response.text


def parse_post(data: Dict) -> Dict:
    print("parsing post data {}", data['shortcode'])
    result = jmespath.search("""{
        id: id,
        shortcode: shortcode,
        src: display_url,
        video_url: video_url,
        taken_at: taken_at_timestamp,
        is_video: is_video,
        captions: edge_media_to_caption.edges[0].node.text
        username: owner.username,
        full_name: owner.full_name,
        profile_pic_url: owner.profile_pic_url,
        videos_url: edge_sidecar_to_children.edges[?is_video==true].node.video_url,
        images_url: edge_sidecar_to_children.edges[?is_video==false].node.display_url
    }""", data)
    return result


def fetch_data_from_graphql(url):
    pattern = r"/(reel|p)/([^/]+)/?"
    match = re.search(pattern, url)

    if not match:
        return None
    shortcode = match.group(2)
    response_dict = scrape_post(shortcode)
    post_dict = parse_post(response_dict)

    images_url = []
    videos_url = []

    if post_dict["is_video"]:
        videos_url.append(shorten_url(post_dict["video_url"]))
    else:
        images_url = post_dict["images_url"]
        videos_url = [shorten_url(video_url) for video_url in post_dict["videos_url"]]

    return SnsInfo(post_link=url,
                   profile=Profile(name=f"{post_dict['full_name']} (@{post_dict['username']})",
                                   url=post_dict['profile_pic_url']),
                   content=post_dict['captions'], images=images_url, videos=videos_url,
                   timestamp=datetime.fromtimestamp(post_dict['taken_at']))


def scrape_post(shortcode: str) -> Dict:
    print(f"scraping instagram post: {shortcode}")

    variables = {
        "shortcode": shortcode
    }
    url = "https://www.instagram.com/graphql/query/?query_hash=b3055c01b4b222b8a47dc12b090e4e64&variables="
    ua = UserAgent()
    user_agent = ua.random
    headers = {"x-ig-app-id": INSTAGRAM_APP_ID, 'user-agent': user_agent}
    result = httpx.get(
        url=url + quote(json.dumps(variables)),
        headers=headers,
        timeout=30000
    )
    print(f"{result.status_code} {result.content}")
    data = json.loads(result.content)
    return data["data"]["shortcode_media"]
