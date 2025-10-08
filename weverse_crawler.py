from urllib.parse import urlparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from sns_info import SnsInfo, Profile


def fetch_data(url: str):
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    WebDriverWait(driver, 30, 1).until(
        EC.presence_of_element_located((By.CLASS_NAME, "WeverseViewer"))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    # 發文者頭像
    avatar_tag = soup.select_one(".avatar-decorator-_-avatar img")
    avatar_url = avatar_tag["src"] if avatar_tag else None

    # 發文者名稱
    name_tag = soup.select_one(".avatar-decorator-_-title_area .avatar-decorator-_-title")
    author_name = name_tag.get_text(strip=True) if name_tag else None

    # 發文內容：抓所有 p.p，保留 <br> 換行
    text_blocks = []
    for p in soup.select("p.p"):
        text_blocks.append(p.get_text("\n", strip=True))
    post_text = "\n\n".join(text_blocks)

    # 照原始順序抓取所有 WidgetMedia (照片和影片縮圖)
    image_urls = []
    media_divs = soup.select("div.WidgetMedia")
    for div in media_divs:
        img_tag = div.find("img")
        if img_tag and img_tag.get("src"):
            image_urls.append(img_tag["src"])

    # 去除網址 query 參數，保持乾淨
    image_urls = [urlparse(link)._replace(query="").geturl() for link in image_urls]

    return SnsInfo(
        post_link=url,
        profile=Profile(name=author_name, url=avatar_url),
        content=post_text,
        images=image_urls
    )