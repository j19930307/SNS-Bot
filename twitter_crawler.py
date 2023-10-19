***REMOVED***
from time import sleep

from selenium import webdriver
from selenium.webdriver import ChromeOptions, Keys
from bs4 import BeautifulSoup

from SnsInfo import SnsInfo, Profile


def fetch_data_from_tweet(tweet_url: str):
    options = ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(tweet_url)

    sleep(7)

    html = driver.page_source
    start = html.index("<html")
    end = html.index("</html>") + 7
    print(html[start:end])
    soup = BeautifulSoup(html[start:end], 'lxml')
    description = soup.find("meta", property="og:description")
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
***REMOVED***
                print("无法找到指定的子字符串")

    # tweet_profile = get_profile_from_tweet(tweet_url)

    profile_name = ""
    twitter_id = ""
    profile_image = ""

    # 取得 twitter 名稱
    div_tag = soup.find('div', class_='css-1dbjc4n r-zl2h9q')
    # 在这个div标签中找到包含文本的<span>标签并获取其文本内容
    if div_tag:
        span_tag = div_tag.find('span', class_='css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0')
        if span_tag:
            profile_name = span_tag.text
    ***REMOVED***
            print("Twitter handle not found inside the div.")
***REMOVED***
        print("Div with specified class not found in the HTML.")

    # 取得 twitter id
    pattern = r'https://twitter\.com/(\w+)/status/\d+'
    # 使用re.search来查找匹配
    match = re.search(pattern, tweet_url)
***REMOVED***
        twitter_id = match.group(1)
***REMOVED***
        print("Twitter username not found in the URL.")

    # 取得 twitter 頭像
    div_tag = soup.find('div', class_='css-1dbjc4n')

    if div_tag:
        # 在该<div>元素中找到图片URL
        profile_image = div_tag.find('img', class_='css-9pa8cd')['src']
***REMOVED***
        print("Div with specified class not found in the HTML.")

    return SnsInfo(post_link=tweet_url, profile=Profile(f"{profile_name} (@{twitter_id})", profile_image),
                   content=description["content"], images=images)


def get_discord_webhook(tweet_url: str):
    if "CUBE_LIGHTSUM" in tweet_url:
***REMOVED*** "https://discord.com/api/webhooks/1162632189553410149/-jjVQRTX3kIhzDbOHecPMi6cOtqixrmS964LOsY082ymcYyDS5lvoyCnuF0FVZu3aZFW"
    elif "STAYC_official" in tweet_url or "STAYC_talk" in tweet_url:
***REMOVED*** "https://discord.com/api/webhooks/1162736592457310268/9UDH3V-4VhKACIOXvkzEmc-1M-9Sj5o94sOlIewtGWj0WsaEuVFBrpynWNBLNsCnEesk"
    elif "_EL7ZUPofficial" in tweet_url:
***REMOVED*** "https://discord.com/api/webhooks/1152119906981126174/AE_mVQ_WF_DZowhiS8lDSpcZipiy8lM74z7LflPOzbKfE-auqAKiVbimcb-dkxXooOTK"


def get_profile_from_tweet(tweet_url: str):
    if "CUBE_LIGHTSUM" in tweet_url:
***REMOVED*** "LIGHTSUM·라잇썸 (@CUBE_LIGHTSUM)", "https://pbs.twimg.com/profile_images/1704148378870026240/3gLE-6ta_400x400.jpg"
    elif "STAYC_official" in tweet_url:
***REMOVED*** "STAYC(스테이씨) (@STAYC_official)", "https://pbs.twimg.com/profile_images/1683115325875949569/XLbXmPdE_400x400.jpg"
    elif "STAYC_talk" in tweet_url:
***REMOVED*** "STAYC (@STAYC_talk)", "https://pbs.twimg.com/profile_images/1655501267630981121/P9xprmtw_400x400.jpg"
    elif "_EL7ZUPofficial" in tweet_url:
***REMOVED*** "EL7Z UP OFFICIAL (_EL7ZUPofficial)", "https://pbs.twimg.com/profile_images/1691461887291162624/dtlS3dKA_400x400.jpg"