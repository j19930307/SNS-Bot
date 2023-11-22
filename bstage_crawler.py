import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By

from SnsInfo import SnsInfo, Profile


def fetch_data(url: str):
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(url)

    driver.find_element(By.CSS_SELECTOR, 'script#__NEXT_DATA__')

    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')

    # 找到指定id的script标签
    script_tag = soup.find('script', id='__NEXT_DATA__')
    if script_tag:
        # 获取script标签内的文本内容
        script_content = script_tag.string
        # 将文本内容解析为JSON
        data = json.loads(script_content)
        post = data["props"]["pageProps"].get("post")
        contents = data["props"]["pageProps"].get("contents")
        if post is not None:
            # 现在您可以访问JSON数据中的字段
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
        elif contents is not None:
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
            author = data["props"]["pageProps"]["space"]["id"]
            author_image = data["props"]["pageProps"]["space"]["faviconImgPath"]
    ***REMOVED*** SnsInfo(post_link=url, profile=Profile(name=author, url=author_image), content=content,
                           images=images_url, videos=videos_url, title=title)
