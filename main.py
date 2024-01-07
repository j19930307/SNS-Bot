import os
import re

import discord
import pyotp
from instagrapi import Client

import bstage_crawler
import instagram_crawler
import twitter_crawler
import twitter_graphql_crawler
import weverse_crawler
from discord_bot import (mentions, generate_embeds, DOMAIN_WEVERSE, DOMAIN_INSTAGRAM, DOMAIN_TWITTER, DOMAIN_X,
                         DOMAIN_BSTAGE)

BOT_TOKEN = os.environ["BOT_TOKEN"]

# client是跟discord連接，intents是要求機器人的權限
intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)

cl = Client()


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
    # Instagram 登入有問題
    # instagram_login()


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
                    pattern = r'(https://' + re.escape(domain) + r'/[^?]+)'
                    match = re.search(pattern, message.content)
                    if match:
                        tweet_url = match.group(1)
                        await message.delete()
                        loading_message = await message.channel.send(content="處理中，請稍後...")
                        if tweet_url:
                            print("提取的推文連結:", tweet_url)
                            try:
                                sns_info = twitter_graphql_crawler.fetch_data(tweet_url)
                                await message.channel.send(content=tweet_url,
                                                           embeds=generate_embeds(username, sns_info))
                                if len(sns_info.videos) > 0:
                                    await message.channel.send(content="\n".join(sns_info.videos))
                                await loading_message.delete()
                            except Exception as e:
                                if hasattr(e, 'message'):
                                    print(e.message)
                                else:
                                    print(e)
                                sns_info = twitter_crawler.fetch_data(tweet_url)
                                await message.channel.send(content=tweet_url,
                                                           embeds=generate_embeds(username, sns_info))
                                await loading_message.delete()
                        else:
                            print("未找到推文連結")
                            await loading_message.delete()
                elif domain == DOMAIN_INSTAGRAM:
                    match = re.search(r'(https://www.instagram.com/[^?]+)', message.content)
                    if match:
                        instagram_url = match.group(0)
                        await message.delete()
                        loading_message = await message.channel.send(content="處理中，請稍後...")
                        if instagram_url:
                            print("提取的推文連結:", instagram_url)
                            try:
                                await message.channel.send(content=instagram_url,
                                                           embeds=generate_embeds(username,
                                                                                  instagram_crawler.fetch_data(cl,
                                                                                                               instagram_url)))
                                await loading_message.delete()
                            except:
                                await loading_message.delete()
                        else:
                            print("未找到推文連結")
                            await loading_message.delete()
                elif domain == DOMAIN_WEVERSE:
                    match = re.search(r'(https://weverse.io/[^?]+)', message.content)
                    if match:
                        weverse_url = match.group(0)
                        await message.delete()
                        loading_message = await message.channel.send(content="處理中，請稍後...")
                        if weverse_url:
                            print("提取的推文連結:", weverse_url)
                            try:
                                await message.channel.send(content=weverse_url,
                                                           embeds=generate_embeds(username,
                                                                                  weverse_crawler.fetch_data(
                                                                                      weverse_url)))
                                await loading_message.delete()
                            except:
                                await loading_message.delete()
                        else:
                            print("未找到推文連結")
                            await loading_message.delete()
                elif domain in DOMAIN_BSTAGE:
                    pattern = r'(https://' + re.escape(domain) + r'/(story/feed/[^?]+|contents/[^?]+))'
                    match = re.search(pattern, message.content)
                    if match:
                        bstage_url = match.group(1)
                        await message.delete()
                        loading_message = await message.channel.send(content="處理中，請稍後...")
                        if bstage_url:
                            print("提取的推文連結:", bstage_url)
                            try:
                                sns_info = bstage_crawler.fetch_data(bstage_url)
                                content_list = [bstage_url]
                                if sns_info.videos is not None:
                                    content_list.extend(sns_info.videos)
                                await message.channel.send(content="\n".join(content_list),
                                                           embeds=generate_embeds(username, sns_info))
                                await loading_message.delete()
                            except:
                                await loading_message.delete()
                        else:
                            print("未找到推文連結")
                            await loading_message.delete()
                else:
                    print("無法提取域名")


client.run(BOT_TOKEN)
