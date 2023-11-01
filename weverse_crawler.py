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

    driver.find_element(By.CLASS_NAME, "WeverseViewer")

    html = driver.page_source

    soup = BeautifulSoup(html, 'lxml')
    # 發文者頭像
    profile_image = soup.find('img', {'class': 'ProfileThumbnailView_thumbnail__8W3E7'})["src"]
    # 發文者名稱
    profile_name = soup.find('strong', class_='PostHeaderView_nickname__6Cb7X').text
    # 發文內容
    content = soup.find('p', class_='p').text
    # 發文所有圖片
    img_tags = soup.find_all('img', class_='photo')
    image_links = [img['src'] for img in img_tags]
    # 發文所有影片縮圖
    img_tag = soup.find('img', class_='PostPreviewVideoThumbnailView_thumbnail__dj7KA')
    if img_tag:
        image_links.append(img_tag['src'])

    return SnsInfo(post_link=url, profile=Profile(name=profile_name, url=profile_image),
                   content=content, images=image_links)
