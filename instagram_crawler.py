import re
from datetime import datetime
import requests
import jmespath
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from sns_info import SnsInfo, Profile
import json
from typing import Dict
from urllib.parse import quote
import httpx


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
    response_dict = scrape_post_by_embed(shortcode)
    if not response_dict:
        return

    post_dict = parse_post(response_dict)
    images_url = []
    videos_url = []

    if post_dict["is_video"]:
        videos_url.append(shorten_url(post_dict["video_url"]))
    else:
        images_url = post_dict["images_url"]
        videos_url = [shorten_url(video_url) for video_url in post_dict["videos_url"]]

    return SnsInfo(post_link=url,
                   profile=Profile(name=f"{post_dict['username']}",
                                   url=post_dict['profile_pic_url']),
                   content=post_dict['captions'], images=images_url, videos=videos_url,
                   timestamp=datetime.fromtimestamp(post_dict['taken_at']))


def scrape_post_by_graphql(shortcode: str) -> Dict:
    print(f"scraping instagram post: {shortcode}")

    variables = {
        "shortcode": shortcode
    }
    url = "https://www.instagram.com/graphql/query/?query_hash=b3055c01b4b222b8a47dc12b090e4e64&variables="
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.instagram.com",
        "Priority": "u=1, i",
        "Sec-Ch-Prefers-Color-Scheme": "dark",
        "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "Sec-Ch-Ua-Full-Version-List": '"Google Chrome";v="125.0.6422.142", "Chromium";v="125.0.6422.142", "Not.A/Brand";v="24.0.0.0"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Model": '""',
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Ch-Ua-Platform-Version": '"12.7.4"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "X-Asbd-Id": "129477",
        "X-Bloks-Version-Id": "e2004666934296f275a5c6b2c9477b63c80977c7cc0fd4b9867cb37e36092b68",
        "X-Fb-Friendly-Name": "PolarisPostActionLoadPostQueryQuery",
        "X-Ig-App-Id": "936619743392459"
    }
    result = httpx.get(
        url=url + quote(json.dumps(variables)),
        headers=headers,
        timeout=30000
    )
    print(f"{result.status_code} {result.content}")
    data = json.loads(result.content)
    return data["data"]["shortcode_media"]


def scrape_post_by_embed(shortcode: str):
    url = f"https://www.instagram.com/p/{shortcode}/embed/captioned"
    result = requests.get(url)

    if result.status_code != 200:
        return print(f"抓取失敗 status code: {result.status_code} 錯誤訊息: {result.content}")

    soup = BeautifulSoup(result.content, 'lxml')
    script_tag = soup.find('script', string=re.compile(r's.handle'))
    if script_tag is None:
        return
    match = re.search(r's\.handle\((\{.*?})\);', script_tag.string, re.DOTALL)

    if match:
        json_str = match.group(1)
        data = json.loads(json_str)
        context_json = data["require"][1][3][0].get("contextJSON")
        if context_json:
            context_dict = json.loads(context_json)
            gql_data = context_dict["gql_data"]
            if gql_data:
                return gql_data["shortcode_media"]