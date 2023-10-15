from selenium import webdriver
from selenium.webdriver import ChromeOptions, Keys
from bs4 import BeautifulSoup


def fetch_data_from_tweet(tweet_url: str):
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(tweet_url)

    html = driver.page_source
    start = html.index("<html")
    end = html.index("</html>") + 7
    soup = BeautifulSoup(html[start:end], 'lxml')
    description = soup.find("meta", property="og:description")
    images = []
    for data in soup.find_all("img", {"class": "css-9pa8cd"}):
        image_url = data["src"]
        if "profile_images" not in image_url:
            images.append(image_url)
    return description["content"], images


def get_discord_webhook(tweet_url: str):
    if "CUBE_LIGHTSUM" in tweet_url:
***REMOVED*** "https://discord.com/api/webhooks/1162632189553410149/-jjVQRTX3kIhzDbOHecPMi6cOtqixrmS964LOsY082ymcYyDS5lvoyCnuF0FVZu3aZFW"
    elif "STAYC_official" in tweet_url or "STAYC_talk" in tweet_url:
***REMOVED*** "https://discord.com/api/webhooks/1162736592457310268/9UDH3V-4VhKACIOXvkzEmc-1M-9Sj5o94sOlIewtGWj0WsaEuVFBrpynWNBLNsCnEesk"


def get_profile_from_tweet(tweet_url: str):
    if "CUBE_LIGHTSUM" in tweet_url:
***REMOVED*** "LIGHTSUM·라잇썸 (@CUBE_LIGHTSUM)", "https://pbs.twimg.com/profile_images/1704148378870026240/3gLE-6ta_400x400.jpg"
    elif "STAYC_official" in tweet_url:
***REMOVED*** "STAYC(스테이씨) (@STAYC_official)", "https://pbs.twimg.com/profile_images/1683115325875949569/XLbXmPdE_400x400.jpg"
    elif "STAYC_talk" in tweet_url:
***REMOVED*** "STAYC (@STAYC_talk)", "https://pbs.twimg.com/profile_images/1655501267630981121/P9xprmtw_400x400.jpg"
