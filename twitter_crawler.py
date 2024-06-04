import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from tweety import Twitter

from sns_info import SnsInfo, Profile


def fetch_data_from_fixtwitter(screen_name: str, tweet_id: str) -> SnsInfo:
    ua = UserAgent()
    user_agent = ua.random
    headers = {'user-agent': user_agent}

    data = requests.get(headers=headers, url=f"https://api.fxtwitter.com/{screen_name}/status/{tweet_id}")
    tweet_dict = json.loads(data.text)

    photos_url = []
    videos_url = []

    if tweet_dict["code"] == 200:
        author = tweet_dict["tweet"]["author"]
        author_name = author["name"]
        author_avatar_url = author["avatar_url"]
        tweet_content = tweet_dict["tweet"]["text"]
        media = tweet_dict["tweet"].get("media")
        if media is not None:
            photos = media.get("photos")
            if photos is not None:
                photos_url = [photo["url"] for photo in photos]
            videos = media.get("videos")
            if videos is not None:
                videos_url = [video["url"] for video in videos]
            created_timestamp_in_seconds = int(tweet_dict["tweet"]["created_timestamp"])
            return SnsInfo(post_link=f"https://x.com/{screen_name}/status/{tweet_id}",
                           profile=Profile(name=f"{author_name} (@{screen_name})", url=author_avatar_url),
                           content=tweet_content, images=photos_url, videos=videos_url,
                           timestamp=datetime.fromtimestamp(created_timestamp_in_seconds))


def fetch_data_from_tweety(url: str):
    app = Twitter("session")
    tweet = app.tweet_detail(url)

    images = []
    videos = []
    for media in tweet.media:
        if media.type == "video" or media.type == "animated_gif":
            # 使用max()函数找出bitrate最大的URL
            video_url = max(media.streams, key=lambda x: x.bitrate).url
            videos.append(video_url)
        else:
            image_url = media.media_url_https + ":orig"
            images.append(image_url)

    return SnsInfo(post_link=url, profile=Profile(f"{tweet.author.name} (@{tweet.author.username})",
                                                  tweet.author.profile_image_url_https), content=tweet.text,
                   images=images, videos=videos)


def fetch_data_from_browser(url: str):
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(url)

    driver.find_element(By.CLASS_NAME, "css-9pa8cd")

    html = driver.page_source
    start = html.index("<html")
    end = html.index("</html>") + 7
    # print(html[start:end])
    soup = BeautifulSoup(html[start:end], 'lxml')
    og_title_content = soup.find("meta", property="og:title")["content"]
    # 找到雙引號的索引位置
    start_quote = og_title_content.find('"')
    end_quote = og_title_content.rfind('"')
    # 使用切片取出雙引號內的內容
    description = og_title_content[start_quote + 1: end_quote]

    images = []
    for data in soup.find_all("img", {"class": "css-9pa8cd"}):
        image_url = data["src"]
        if "profile_images" not in image_url:
            # 查找子字符串 "?format=jpg" 的索引
            index = image_url.find("?format=jpg")
            if index != -1:
                # 从原始 URL 中截取子字符串
                modified_url = image_url[:index + len("?format=jpg")]
                images.append(modified_url)
            else:
                print("无法找到指定的子字符串")

    profile_name = ""
    twitter_id = ""
    profile_image = ""

    # 取得 twitter 名稱
    div_tag = soup.find('div', class_='css-175oi2r r-zl2h9q')
    if div_tag:
        span_tag = div_tag.find('span', class_='css-1qaijid r-bcqeeo r-qvutc0 r-poiln3')
        if span_tag:
            profile_name = span_tag.text
        else:
            print("Twitter handle not found inside the div.")
    else:
        print("Div with specified class not found in the HTML.")

    # 取得 twitter id
    pattern = r'https://twitter\.com/(\w+)/status/\d+'
    # 使用re.search来查找匹配
    match = re.search(pattern, url)
    if match:
        twitter_id = match.group(1)
    else:
        print("Twitter username not found in the URL.")

    # 取得 twitter 頭像
    div_tag = soup.find('div',
                        class_='css-175oi2r r-1adg3ll r-1pi2tsx r-13qz1uu r-u8s1d r-1wyvozj r-1v2oles r-desppf r-bztko3')

    if div_tag:
        profile_image = div_tag.find('img', class_='css-9pa8cd')['src']
    else:
        print("Div with specified class not found in the HTML.")

    return SnsInfo(post_link=url, profile=Profile(f"{profile_name} (@{twitter_id})", profile_image),
                   content=description, images=images)


def fetch_data(url: str):
    match = re.match("https://(twitter|x).com/(.+)/status/(\\d+)", url)
    if not match:
        return None

    screen_name = match.group(2)
    tweet_id = match.group(3)

    sns_info = fetch_data_from_fixtwitter(screen_name, tweet_id)
    if sns_info is not None:
        return sns_info

    sns_info = fetch_data_from_tweety(url)
    if sns_info is not None:
        return sns_info

    sns_info = fetch_data_from_browser(url)
    return sns_info
