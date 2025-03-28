import json
import re
from typing import Dict

import jmespath
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from fake_useragent import UserAgent

from sns_info import SnsInfo, Profile


def fetch_data(url: str):
    match = re.search(r"https?://([^/]+)/story/feed/([\w\d]+)", url)
    if match:
        domain = match.group(1)
        post_id = match.group(2)
        parts = re.split(r"[.-]", domain)
        artist = parts[0]

        ua = UserAgent()
        user_agent = ua.random
        headers = {'user-agent': user_agent}
        response = requests.get(url=f"https://{domain}/svc/home/api/v1/home/star/feeds",
                                headers=headers)

        data = json.loads(response.text)
        for item in data.get("items"):
            if item.get("typeId") == post_id:
                post = parse_post(item)
                images = []
                videos = []
                if post.get("images"):
                    images.extend(post["images"])
                if post.get("video_thumbnail"):
                    images.append(f"https://image.static.bstage.in/cdn-cgi/image/metadata=none/{artist}" + post[
                        "video_thumbnail"])
                if post.get("video"):
                    videos.append(f"https://media.static.bstage.in/{artist}" + post["video"])
                return SnsInfo(post_link=url, profile=Profile(name=post["auther_name"], url=post["auther_image_url"]),
                               content=post["content"], images=images, videos=videos,
                               timestamp=parser.isoparse(post["published_at"]))


def parse_post(data: Dict) -> Dict:
    return jmespath.search(
        """{
        auther_name: author.nickname,
        auther_image_url: author.avatarImgPath,
        content: description,
        images: images,
        video: video.hlsPath.path
        video_thumbnail: video.thumbnailPaths[0].path
        published_at: publishedAt
    }""",
        data
    )


if __name__ == "__main__":
    print(fetch_data("https://gyubin.bstage.in/story/feed/67cc3489695e7d3734e427d7"))
