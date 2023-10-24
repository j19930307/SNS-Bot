***REMOVED***
***REMOVED***

***REMOVED***
from discord import message, Embed

***REMOVED***
from discord_bot import post_source

BOT_TOKEN = os.environ["DISCORD_WEBHOOK"]

# client是跟discord連接，intents是要求機器人的權限
intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)


def generate_embeds(tweet_url: str):
    sns_info = twitter_crawler.fetch_data_from_tweet(tweet_url)
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
    return embeds


# 調用event函式庫
@client.event
# 當機器人完成啟動
***REMOVED***
    print(f"目前登入身份 --> {client.user}")


@client.event
# 當頻道有新訊息
***REMOVED***
***REMOVED***
***REMOVED***
    if message.author == client.user:
***REMOVED***
    for role in message.role_mentions:
        for member in role.members:
            if member.id == client.user.id:
                # 新訊息包含Hello，回覆Hello, world!
                if "twitter" in message.content:
    ***REMOVED***
                    tweet_url = re.search(r'(https://twitter.com/[^?]+)', message.content)
    ***REMOVED***
                        print("提取的推文链接:", tweet_url.group(0))
                        await message.channel.send(content=tweet_url.group(0), embeds=generate_embeds(tweet_url.group(0)))
    ***REMOVED***
                        print("未找到推文链接")
                    # await message.channel.send("開始解析")


client.run(BOT_TOKEN)
