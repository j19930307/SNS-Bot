from time import sleep

from selenium import webdriver
from selenium.webdriver import ChromeOptions, Keys
from bs4 import BeautifulSoup
***REMOVED***_bot
from SnsInfo import SnsInfo, Profile


def fetch_data_from_weverse(url: str):
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(url)

    sleep(7)

    html = driver.page_source
    # print(html)

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
***REMOVED***
        print("Video Thumbnail URL not found in the HTML.")

    return SnsInfo(post_link=url, profile=Profile(name=profile_name, url=profile_image),
                   content=content, images=image_links)


def get_discord_webhook(url: str):
    if "lightsum" in url:
***REMOVED*** "https://discord.com/api/webhooks/1162632189553410149/-jjVQRTX3kIhzDbOHecPMi6cOtqixrmS964LOsY082ymcYyDS5lvoyCnuF0FVZu3aZFW"
    elif "stayc" in url:
***REMOVED*** "https://discord.com/api/webhooks/1162736592457310268/9UDH3V-4VhKACIOXvkzEmc-1M-9Sj5o94sOlIewtGWj0WsaEuVFBrpynWNBLNsCnEesk"
    # elif "_EL7ZUPofficial" in tweet_url:
    #     return "https://discord.com/api/webhooks/1152119906981126174/AE_mVQ_WF_DZowhiS8lDSpcZipiy8lM74z7LflPOzbKfE-auqAKiVbimcb-dkxXooOTK"
