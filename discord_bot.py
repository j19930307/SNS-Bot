import json

***REMOVED***quests

from discord_message import Embed, Author, Image, Message

# 自定义 JSON 编码函数
def custom_encoder(obj):
    if isinstance(obj, (Author, Image, Embed, Message)):
***REMOVED*** obj.__dict__
***REMOVED***
        raise TypeError("Object is not JSON serializable")


# 發送訊息到 Discord
def send_message(webhook_url: str, link: str, profile_name: str, profile_image_url: str, content: str, images: list):
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
            embeds.append(
                Embed(Author(profile_name, profile_image_url), content, image=Image(url), url=profile_image_url))
    ***REMOVED***
            embeds.append(Embed(image=Image(url), url=profile_image_url))

    # 將 JSON 數據轉換為字符串
    data_json = json.dumps(Message(link, embeds), default=custom_encoder)
    # data_json = json.dumps(Message("", embeds), default=custom_encoder)
    print(data_json)

    # 使用 POST 請求將消息發送到 Webhook
    response = requests.post(webhook_url, data=data_json, headers={'Content-Type': 'application/json'})

    # 檢查是否成功發送消息
    if response.status_code == 204:
        print('消息已成功發送到 Discord 頻道！')
***REMOVED***
        print('消息發送失敗。HTTP 響應碼：', response.status_code)
        print('響應內容：', response.text)
