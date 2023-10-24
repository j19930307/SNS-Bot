import json
***REMOVED***

***REMOVED***quests

from SnsInfo import SnsInfo, Profile
# from discord_message import Embed, Author, Image, Message

from discord import Webhook, Embed
import aiohttp


# 自定义 JSON 编码函数
# def custom_encoder(obj):
#     if isinstance(obj, (Author, Image, Embed, Message)):
# ***REMOVED*** obj.__dict__
# ***REMOVED***
#         raise TypeError("Object is not JSON serializable")


# 發送訊息到 Discord
#  def send_message(webhook_url: str):
#     async with aiohttp.ClientSession() as session:
#         webhook = Webhook.from_url(webhook_url, session=session)
#         # 創建 Embed 對象
#         embed = Embed(
#             title='標題',
#             description='這是一個包含圖片的 Embed 訊息',
#             color=0x3498db  # 16進位顏色碼，你可以根據需要更改顏色
#         )
#
#         # 添加圖片到 Embed 中
#         embed.set_image(
#             url='')  # 用你的圖片 URL 替換
#
#         await webhook.send("https://www.google.com", embed=embed)


def post_source(url: str):
    if "twitter.com" in url or "x.com" in url:
***REMOVED*** "X", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/X_icon_2.svg/2048px-X_icon_2.svg.png"
    elif "instagram" in url:
***REMOVED*** "Instagram", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Instagram_icon.png/600px-Instagram_icon.png"
    elif "weverse" in url:
***REMOVED*** "Weverse", "https://image.winudf.com/v2/image1/Y28uYmVueC53ZXZlcnNlX2ljb25fMTY5NjQwNDE0MF8wMTM/icon.webp?w=140&fakeurl=1&type=.webp"


def discord_webhook(channel: str):
    if channel == "STAYC":
***REMOVED*** os.environ["STAYC_WEBHOOK"]
    elif channel == "LIGHTSUM":
***REMOVED*** os.environ["LIGHTSUM_WEBHOOK"]
    elif channel == "EL7Z UP":
***REMOVED*** os.environ["EL7ZUP_WEBHOOK"]


async def send_message(webhook_url: str, sns_info: SnsInfo):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)
        embeds = []
        # 圖片訊息，Embed 的 url 如果一樣，最多可以 4 張以下的合併在一個區塊
        for index, image_url in enumerate(sns_info.images):
            if index == 0:
                embeds.append(
                    Embed(description=sns_info.content, url=sns_info.profile.url)
                    .set_author(name=sns_info.profile.name, icon_url=sns_info.profile.url)
                    .set_image(url=image_url)
                    .set_footer(text=post_source(sns_info.post_link)[0],
                                icon_url=post_source(sns_info.post_link)[1]))
***REMOVED***
                embeds.append(Embed(url=sns_info.profile.url)
                              .set_author(name=sns_info.profile.name, url=sns_info.profile.url)
                              .set_image(url=image_url))
        await webhook.send(content=sns_info.post_link, embeds=embeds)
        print('消息已成功發送到 Discord 頻道！')

# 運行異步函數
# if __name__ == '__main__':
#     import asyncio
#
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(send_message(
#         "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc",
#         SnsInfo("https://www.twitter.com", Profile("發文者名稱", "https://cdn-icons-png.flaticon.com/256/25/25297.png"),
#                 content="發文內容", images=["https://cdn-icons-png.flaticon.com/256/25/25297.png",
#                                             "https://cdn-icons-png.flaticon.com/256/25/25297.png",
#                                             "https://cdn-icons-png.flaticon.com/256/25/25297.png"])))

# def send_message():

#     for index, url in enumerate(sns_info.images):
#         if index == 0:
#             embeds.append(
#                 Embed(Author(sns_info.profile.name, sns_info.profile.url), sns_info.content, image=Image(url),
#                       url=sns_info.profile.url))
#     ***REMOVED***
#             embeds.append(Embed(image=Image(url), url=sns_info.profile.url))
#
#     # 將 JSON 數據轉換為字符串
#     data_json = json.dumps(Message(sns_info.post_link, embeds), default=custom_encoder)
#     # data_json = json.dumps(Message("", embeds), default=custom_encoder)
#     print(data_json)
#
#     # 使用 POST 請求將消息發送到 Webhook
#     response = requests.post(webhook_url, data=data_json, headers={'Content-Type': 'application/json'})
#
#     # 檢查是否成功發送消息
#     if response.status_code == 204:
#         print('消息已成功發送到 Discord 頻道！')
# ***REMOVED***
#         print('消息發送失敗。HTTP 響應碼：', response.status_code)
#         print('響應內容：', response.text)
