***REMOVED***

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
***REMOVED***
                print("无法找到指定的子字符串")

    # tweet_profile = get_profile_from_tweet(tweet_url)

    profile_name = ""
    twitter_id = ""
    profile_image = ""

    # 取得 twitter 名稱
    div_tag = soup.find('div', class_='css-175oi2r r-zl2h9q')
    # 在这个div标签中找到包含文本的<span>标签并获取其文本内容
    if div_tag:
        span_tag = div_tag.find('span', class_='css-1qaijid r-bcqeeo r-qvutc0 r-poiln3')
        if span_tag:
            profile_name = span_tag.text
    ***REMOVED***
            print("Twitter handle not found inside the div.")
***REMOVED***
        print("Div with specified class not found in the HTML.")

    # 取得 twitter id
    pattern = r'https://twitter\.com/(\w+)/status/\d+'
    # 使用re.search来查找匹配
    match = re.search(pattern, url)
***REMOVED***
        twitter_id = match.group(1)
***REMOVED***
        print("Twitter username not found in the URL.")

    # 取得 twitter 頭像
    div_tag = soup.find('div', class_='css-175oi2r r-1adg3ll r-1pi2tsx r-13qz1uu r-u8s1d r-1wyvozj r-1v2oles r-desppf r-bztko3')

    if div_tag:
        # 在该<div>元素中找到图片URL
        profile_image = div_tag.find('img', class_='css-9pa8cd')['src']
***REMOVED***
        print("Div with specified class not found in the HTML.")

    return SnsInfo(post_link=url, profile=Profile(f"{profile_name} (@{twitter_id})", profile_image),
                   content=description, images=images)