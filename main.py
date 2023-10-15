import json
from datetime import datetime

import instaloader
import pytz
import requests

from discord_message import Message, Embed, Image, Author

# 創建 Instaloader 實例
L = instaloader.Instaloader()
# L.login("hungchihung1990", "gaeun940820")

# 測試
# webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"
#STAYC
# webhook_url = "https://discord.com/api/webhooks/1162736592457310268/9UDH3V-4VhKACIOXvkzEmc-1M-9Sj5o94sOlIewtGWj0WsaEuVFBrpynWNBLNsCnEesk"
#LIGHTSUM
webhook_url = "https://discord.com/api/webhooks/1162632189553410149/-jjVQRTX3kIhzDbOHecPMi6cOtqixrmS964LOsY082ymcYyDS5lvoyCnuF0FVZu3aZFW"

# 輸入要下載的帳戶名稱
profile = "stayc_highup"


def read_last_updated():
    with open('last_updated.txt', 'r') as f:
        created_time = f.read()
        f.close()
        return created_time


# write text to last_updated.txt
def write_last_updated(text: str):
    with open('last_updated.txt', 'w') as f:
        f.write(text)
        f.close()


def compare_times(time_str1: str, time_str2: str):
    # 將時間字符串轉換為datetime對象
    time1 = datetime.fromisoformat(time_str1[:-1])  # 去掉最後的 'Z' 字符再轉換
    time2 = datetime.fromisoformat(time_str2[:-1])
    # 進行比較並返回結果
    return time1 > time2


# 自定义 JSON 编码函数
def custom_encoder(obj):
    if isinstance(obj, (Author, Image, Embed, Message)):
        return obj.__dict__
    else:
        raise TypeError("Object is not JSON serializable")



link = "https://twitter.com/CUBE_LIGHTSUM/status/1713375273788522884"
content = """
[#주현] 오늘 하루도 행복하쟈 썸잇 🤍☁️
"""

images = []
with open("tweet.txt") as text_file:
    for line in text_file:
        line = line.replace("&name=small\n", "")
        images.append(line)

# STAYC 官方
# profile_image = "https://pbs.twimg.com/profile_images/1683115325875949569/XLbXmPdE_400x400.jpg"
# account = "STAYC(스테이씨) (@STAYC_official)"

# STAYC 成員
# profile_image = "https://pbs.twimg.com/profile_images/1655501267630981121/P9xprmtw_400x400.jpg"
# account = "STAYC (@STAYC_talk)"

# LIGHTSUM 官方
# profile_image = "https://pbs.twimg.com/profile_images/1704148378870026240/3gLE-6ta_400x400.jpg"
# account = "LIGHTSUM·라잇썸 (@CUBE_LIGHTSUM)"

# 發送訊息到 Discord
def send_message(link: str, content: str, images: list):
    # Discord Webhook URL，請將 URL 替換為您自己的 Webhook URL

    # 获取 "content" 字段的数据
    # content_data = instagram_url
    # images_url = post.get("images", [])
    # nickname = post["writer"]["nickname"]
    # profile_image = post["writer"]["profileImage"]

    embeds = []

    # 構建要發送的 JSON 數據
    # 文字訊息
    # if len(images_url) == 0:
    # embeds.append(Embed(Author("stayc", ""), content_data))
    # elif len(images_url) == 1:
    #     embeds.append(Embed(Author(nickname, profile_image), content_data, image=Image(images_url[0])))
    # else:
    #     embeds.append(
    #         Embed(Author(nickname, profile_image), content_data, image=Image(images_url[0]), url=profile_image))
    #     for i in range(1, len(images_url)):
    #         embeds.append(Embed(image=Image(images_url[i]), url=profile_image))

    # if len(images) > 0:
    #     for image in images:
    #         embeds.append(Embed(image=Image(image), url=profile_image))

    # 圖片訊息，Embed 的 url 如果一樣，最多可以 4 張以下的合併在一個區塊
    for index, url in enumerate(images):
        if index == 0:
            embeds.append(Embed(Author(account, profile_image), content, image=Image(url), url=profile_image))
        else:
            embeds.append(Embed(image=Image(url), url=profile_image))

    # 將 JSON 數據轉換為字符串
    data_json = json.dumps(Message(link, embeds), default=custom_encoder)
    # data_json = json.dumps(Message("", embeds), default=custom_encoder)
    print(data_json)

    # 使用 POST 請求將消息發送到 Webhook
    response = requests.post(webhook_url, data=data_json, headers={'Content-Type': 'application/json'})

    # 檢查是否成功發送消息
    if response.status_code == 204:
        print('消息已成功發送到 Discord 頻道！')
    else:
        print('消息發送失敗。HTTP 響應碼：', response.status_code)
        print('響應內容：', response.text)


# 獲取帳戶的信息
# user = instaloader.Profile.from_username(L.context, profile)

# sorted(user.get_posts(), key=lambda p: -p.date_utc)

# 遍歷並打印帳戶的帖子
# all_post = user.get_posts()
# for index, post in enumerate(all_post):
#     last_updated = read_last_updated()
#     if not post.is_pinned:
#         create_time = post.date_utc
#         if last_updated < str(create_time):
#             images_or_videos_url = []
#             for image in post.get_sidecar_nodes():
#                 if image.is_video:
#                     # 如果是视频，获取视频链接
#                     video_url = image.video_url
#                     images_or_videos_url.append(video_url)
#                 else:
#                     # 如果是图片，获取图片链接
#                     img_url = image.display_url
#                     images_or_videos_url.append(img_url)
#             print((post.caption, images_or_videos_url, create_time))
#             write_last_updated(str(create_time))
#             send_message(post.url)
#         else:
#             print("抓取完成")
#             break

send_message(link, content, images)
