import json
from time import sleep

from selenium import webdriver
from selenium.webdriver import ChromeOptions, Keys
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from discord_bot ***REMOVED***_webhook
from SnsInfo import SnsInfo, Profile


def fetch_data(url: str):
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(url)

    driver.find_element(By.ID, "__NEXT_DATA__")

    html = driver.page_source

    soup = BeautifulSoup(html, 'lxml')

    # 找到指定id的script标签
    script_tag = soup.find('script', id='__NEXT_DATA__')
    if script_tag:
        # 获取script标签内的文本内容
        script_content = script_tag.string
        # 将文本内容解析为JSON
        data = json.loads(script_content)
        # 现在您可以访问JSON数据中的字段
        content = data["props"]["pageProps"]["post"]["body"]
        poster_name = data["props"]["pageProps"]["post"]["author"]["nickname"]
        poster_image_url = data["props"]["pageProps"]["post"]["author"]["avatarImgPath"]
        images_url = data["props"]["pageProps"]["post"]["images"]
***REMOVED*** SnsInfo(post_link=url, profile=Profile(name=poster_name, url=poster_image_url), content=content,
                       images=images_url)
***REMOVED***
        print("未找到指定id的script标签")
