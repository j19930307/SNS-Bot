import os
import re

import discord
from discord import message, Embed

import instagram_crawler
import twitter_crawler
import weverse_crawler
from SnsInfo import SnsInfo
from discord_bot import post_source

BOT_TOKEN = os.environ["BOT_TOKEN"]

# client是跟discord連接，intents是要求機器人的權限
intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)


def generate_embeds(sns_info: SnsInfo):
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
        else:
            embeds.append(Embed(url=sns_info.profile.url)
                          .set_author(name=sns_info.profile.name, url=sns_info.profile.url)
                          .set_image(url=image_url))
    return embeds


def mentions(message: message, id: int):
    if id in message.raw_mentions:
        return True
    else:
        for role in message.role_mentions:
            for member in role.members:
                if member.id == client.user.id:
                    return True
    return False


# 調用event函式庫
@client.event
# 當機器人完成啟動
async def on_ready():
    print(f"目前登入身份 --> {client.user}")


@client.event
# 當頻道有新訊息
async def on_message(message):
    # 排除機器人本身的訊息，避免無限循環
    # role_mentions.member.id
    if message.author == client.user:
        return
    # 判斷是否有 @bot
    if mentions(message, client.user.id):
        if "close" in message.content:
            await client.close()
        elif "twitter.com" in message.content or "x.com" in message.content:
            await message.delete()
            loading_message = await message.channel.send(content="處理中，請稍後...")
            tweet_url = re.search(r'(https://twitter.com/[^?]+)', message.content)
            if tweet_url:
                print("提取的推文链接:", tweet_url.group(0))
                await message.channel.send(content=tweet_url.group(0), embeds=generate_embeds(
                    twitter_crawler.fetch_data_from_tweet(tweet_url.group(0))))
                await loading_message.delete()
            else:
                print("未找到推文链接")
                await loading_message.delete()
            # await message.channel.send("開始解析")
        elif "instagram.com" in message.content:
            await message.delete()
            loading_message = await message.channel.send(content="處理中，請稍後...")
            instagram_url = re.search(r'(https://www.instagram.com/[^?]+)', message.content)
            if instagram_url:
                print("提取的推文链接:", instagram_url.group(0))
                await message.channel.send(content=instagram_url.group(0),
                                           embeds=generate_embeds(instagram_crawler.fetch_data_from_instagram(
                                               instagram_url.group(0))))
                await loading_message.delete()
            else:
                print("未找到推文链接")
                await loading_message.delete()
        elif "weverse.io" in message.content:
            await message.delete()
            loading_message = await message.channel.send(content="處理中，請稍後...")
            weverse_url = re.search(r'(https://weverse.io/[^?]+)', message.content)
            if weverse_url:
                print("提取的推文链接:", weverse_url.group(0))
                await message.channel.send(content=weverse_url.group(0),
                                           embeds=generate_embeds(weverse_crawler.fetch_data_from_weverse(
                                               weverse_url.group(0))))
                await loading_message.delete()
            else:
                print("未找到推文链接")
                await loading_message.delete()


client.run(BOT_TOKEN)
