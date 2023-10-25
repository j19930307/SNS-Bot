import asyncio

import aiohttp
from discord import Webhook, Embed


async def send_message(webhook_url: str):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)
        embeds = []
        # 圖片訊息，Embed 的 url 如果一樣，最多可以 4 張以下的合併在一個區塊
        media_url = ["https://pbs.twimg.com/ext_tw_video_thumb/1716828766654373888/pu/img/l1uO-NCv-S70HaSu.jpg",
                     "https://video.twimg.com/ext_tw_video/1716828766654373888/pu/vid/avc1/1280x658/zdQroU-ZxL9WVj12.mp4"]

        for index, image_url in enumerate(media_url):
            if index == 0:
                embeds.append(
                    Embed(description="測試",
                          url="https://pbs.twimg.com/ext_tw_video_thumb/1716828766654373888/pu/img/l1uO-NCv-S70HaSu.jpg")
                    .set_author(name="發文者", icon_url="")
                    .set_image(url=image_url))
***REMOVED***
                if "mp4" in image_url:
                    embeds.append(Embed(description="", url="https://video.twimg.com/ext_tw_video/1716828766654373888/pu/vid/avc1/1280x658/zdQroU-ZxL9WVj12.mp4")
                                  .set_thumbnail(url="https://pbs.twimg.com/ext_tw_video_thumb/1716828766654373888/pu/img/l1uO-NCv-S70HaSu.jpg")
                                )
                # embeds.append(Embed(
                #     url="https://pbs.twimg.com/ext_tw_video_thumb/1716828766654373888/pu/img/l1uO-NCv-S70HaSu.jpg")
                #               # .set_author(name=sns_info.profile.name, url=sns_info.profile.url)
                #               .set_image(url=image_url))
                await webhook.send(content="https://www.google.com", embeds=embeds)
                print('消息已成功發送到 Discord 頻道！')


# 測試
webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"

loop = asyncio.get_event_loop()
loop.run_until_complete(send_message(webhook_url=webhook_url))
