import os
import re

import discord
import pyotp
from discord import message, Embed
from instagrapi import Client

import bstage_crawler
import instagram_crawler
import twitter_graphql_crawler
import weverse_crawler
from SnsInfo import SnsInfo
from discord_bot import post_source

BOT_TOKEN = os.environ["BOT_TOKEN"]

# client是跟discord連接，intents是要求機器人的權限
intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)

DOMAIN_TWITTER = "twitter.com"
DOMAIN_X = "x.com"
DOMAIN_INSTAGRAM = "instagram.com"
DOMAIN_WEVERSE = "weverse.io"
DOMAIN_H1KEY = "h1key-official.com"
DOMAIN_YEEUN = "yeeun.bstage.in"

cl = Client()


def generate_embeds(username: str, sns_info: SnsInfo):
    embeds = []
    # 圖片訊息，Embed 的 url 如果一樣，最多可以 4 張以下的合併在一個區塊
    for index, image_url in enumerate(sns_info.images[slice(4)]):
        if index == 0:
            source = post_source(sns_info.post_link)
            embed = (
                Embed(description=sns_info.content, url=sns_info.profile.url).set_author(name=sns_info.profile.name,
                                                                                         icon_url=sns_info.profile.url)
                .set_image(url=image_url)
                .insert_field_at(index=0, name="使用者", value=username))
            if source is not None:
                embed.set_footer(text=post_source(sns_info.post_link)[0],
                                 icon_url=post_source(sns_info.post_link)[1])
            embeds.append(embed)
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


def instagram_login():
    insta_username = os.environ["INSTAGRAM_USERNAME"]
    insta_password = os.environ["INSTAGRAM_PASSWORD"]
    secret = os.environ["INSTAGRAM_SECRET"].replace(" ", "")
    totp = pyotp.TOTP(secret)
    verification_code = totp.now()
    return cl.login(username=insta_username, password=insta_password, verification_code=verification_code)


# 調用event函式庫
@client.event
# 當機器人完成啟動
async def on_ready():
    print(f"目前登入身份 --> {client.user}")
    instagram_login()


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
        else:
            username = message.author.nick
            # 取出 domain
            match = re.search(r'https://(www\.)?([^/]+)', message.content)
            if match:
                domain = match.group(2)
                if domain == DOMAIN_TWITTER or domain == DOMAIN_X:
                    await message.delete()
                    loading_message = await message.channel.send(content="處理中，請稍後...")
                    pattern = r'(https://' + re.escape(domain) + r'/[^?]+)'
                    match = re.search(pattern, message.content)
                    if match:
                        tweet_url = match.group(1)
                        if tweet_url:
                            print("提取的推文链接:", tweet_url)
                            sns_info = twitter_graphql_crawler.fetch_data(tweet_url)
                            await message.channel.send(content=tweet_url, embeds=generate_embeds(username, sns_info))
                            if len(sns_info.videos) > 0:
                                await message.channel.send(content="\n".join(sns_info.videos))
                            await loading_message.delete()
                        else:
                            print("未找到推文链接")
                            await loading_message.delete()
                elif domain == DOMAIN_INSTAGRAM:
                    await message.delete()
                    loading_message = await message.channel.send(content="處理中，請稍後...")
                    instagram_url = re.search(r'(https://www.instagram.com/[^?]+)', message.content)
                    if instagram_url:
                        print("提取的推文链接:", instagram_url.group(0))
                        await message.channel.send(content=instagram_url.group(0),
                                                   embeds=generate_embeds(username,
                                                                          instagram_crawler.fetch_data_from_instagram(
                                                                              cl, instagram_url.group(0))))
                        await loading_message.delete()
                    else:
                        print("未找到推文链接")
                        await loading_message.delete()
                elif domain == DOMAIN_WEVERSE:
                    await message.delete()
                    loading_message = await message.channel.send(content="處理中，請稍後...")
                    weverse_url = re.search(r'(https://weverse.io/[^?]+)', message.content)
                    if weverse_url:
                        print("提取的推文链接:", weverse_url.group(0))
                        await message.channel.send(content=weverse_url.group(0),
                                                   embeds=generate_embeds(username,
                                                                          weverse_crawler.fetch_data_from_weverse(
                                                                              weverse_url.group(0))))
                        await loading_message.delete()
                    else:
                        print("未找到推文链接")
                        await loading_message.delete()
                elif domain == DOMAIN_H1KEY or domain == DOMAIN_YEEUN:
                    await message.delete()
                    loading_message = await message.channel.send(content="處理中，請稍後...")
                    pattern = r'(https://' + re.escape(domain) + r'/story/feed/[^?]+)'
                    match = re.search(pattern, message.content)
                    if match:
                        bstage_url = match.group(1)
                        if bstage_url:
                            print("提取的推文链接:", bstage_url)
                            sns_info = bstage_crawler.fetch_data(bstage_url)
                            content_list = [bstage_url]
                            if sns_info.videos is not None:
                                content_list.extend(sns_info.videos)
                            await message.channel.send(content="\n".join(content_list),
                                                       embeds=generate_embeds(username, sns_info))
                            await loading_message.delete()
                        else:
                            print("未找到推文链接")
                            await loading_message.delete()
                    else:
                        print("无法匹配域名")
                else:
                    print("无法提取域名")


client.run(BOT_TOKEN)
