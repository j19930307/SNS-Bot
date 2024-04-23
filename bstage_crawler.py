import json
***REMOVED***

***REMOVED***quests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from sns_info import SnsInfo, Profile


def fetch_data(url: str):
    match = re.match(r'https://(.*)/(story/feed|contents)/(.*)', url)
    try:
        domain = match.group(1)
        content_id = match.group(3)
        ua = UserAgent()
        user_agent = ua.random
        headers = {'user-agent': user_agent}
        if match.group(2) == "story/feed":
            response = requests.get(
                url=f"https://{domain}/_next/data/HZP_I8FxxAHc5XDHH3dgs/ko/story/feed/{content_id}.json",
                headers=headers)
            data = json.loads(response.text)
            page_props = data["pageProps"]
            post = page_props.get("post")
            if post is not None:
                content = post["body"]
                poster_name = post["author"]["nickname"]
                poster_image_url = post["author"]["avatarImgPath"]
                images_url = []
                videos_url = []
                try:
                    images_url.extend(post["images"])
                except KeyError:
                    print("找不到圖片")
                    images_url.extend(post["video"]["thumbnailPaths"])
                    videos_url.append(post["video"]["hlsPath"])
        ***REMOVED*** SnsInfo(post_link=url, profile=Profile(name=poster_name, url=poster_image_url), content=content,
                               images=images_url, videos=videos_url)
        elif match.group(2) == "contents":
            response = requests.get(
                url=f"https://{domain}/_next/data/Mvb0vi-PA7Tn3acXkiiUv/contents/{content_id}.json",
                headers=headers)
            data = json.loads(response.text)
            page_props = data["pageProps"]
            contents = page_props.get("contents")
            # 標題
            title = contents["title"]
            # 內文 and 圖
            encoded_body = contents["body"]
            images_url = []
            videos_url = []
            soup = BeautifulSoup(encoded_body, 'lxml')
            image_tag = soup.findAll('img')
            if image_tag:
                for tag in image_tag:
                    images_url.append(tag.get('src'))
            # 內文
            content = "\n".join(["\n" if p.text == "\xa0" else p.text for p in soup.findAll("p")])
            # 沒有發文者資訊，用 id 代替
            author = page_props["space"]["id"]
            author_image = page_props["space"]["faviconImgPath"]
    ***REMOVED*** SnsInfo(post_link=url, profile=Profile(name=author, url=author_image), content=content,
                           images=images_url, videos=videos_url, title=title)
    except IndexError:
        print("網址錯誤")