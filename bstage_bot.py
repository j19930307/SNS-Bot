import json
import os
import random
import time

import discord
import requests
from dateutil import parser
from dotenv import load_dotenv
from fake_useragent import UserAgent

import discord_bot
from firebase import Firebase
from models.sns_post import SnsPost, Author
from sns_type import SnsType

ua = UserAgent()
user_agent = ua.random
headers = {'user-agent': user_agent}


def convert_to_datetime(date_string):
    return parser.isoparse(date_string)


class BstageBot:
    def __init__(self, bot: discord.Bot, firestore: Firebase):
        self.__bot = bot
        self.__firestore = firestore

    async def execute(self):
        for doc in self.__firestore.get_subscribed_list(SnsType.BSTAGE):
            # 每隔 3 ~ 5 秒執行
            random_sleep_time = random.uniform(3, 5)
            time.sleep(random_sleep_time)
            artist = doc.id
            discord_channel_id = doc.get("discord_channel_id")
            # 取得上次最新發文時間
            last_updated = doc.get("updated_at")
            print(f"上次發文時間: {last_updated}")
            print("開始抓取資料...")
            request = requests.get(headers=headers,
                                   url=f"https://{artist}.bstage.in/svc/home/api/v1/home/star?page=1&pageSize=10")
            data = json.loads(request.text)

            sns_post_list = []
            for item in data["feeds"]["items"]:
                published_at_datetime = convert_to_datetime(item["publishedAt"])
                if last_updated < published_at_datetime:
                    images = []
                    videos = []
                    if item.get("images") is not None:
                        images += [image for image in item.get("images")]
                    if item.get("video") is not None:
                        images += [
                            f"https://image.static.bstage.in/cdn-cgi/image/metadata=none/{artist}" + thumbnail["path"]
                            for thumbnail in item["video"]["thumbnailPaths"]]
                        videos.append(f"https://media.static.bstage.in/{artist}" + item["video"]["hlsPath"]["path"])
                    sns_post = SnsPost(
                        post_link=f"https://{artist}.bstage.in/story/feed/{item['typeId']}",
                        author=Author(item["author"]["nickname"], item["author"]["avatarImgPath"]),
                        text=item["description"], images=images, videos=videos,
                        created_at=published_at_datetime)
                    print(sns_post)
                    sns_post_list.append(sns_post)
                else:
                    break

            post_count = len(sns_post_list)
            if post_count != 0:
                print(f"有 {post_count} 則發文")
                for sns_post in reversed(sns_post_list):
                    channel = self.__bot.get_channel(discord_channel_id)
                    await channel.send(sns_post.post_link, embeds=discord_bot.generate_embeds(sns_post))
                    videos = sns_post.videos
                    if videos is not None and len(videos) > 0:
                        await channel.send(content="\n".join(sns_post.videos))
                # 儲存最新發文時間
                updated_at = max([sns_post.created_at for sns_post in sns_post_list])
                print(f"更新最後發文時間: {updated_at}")
                self.__firestore.set_updated_at(SnsType.BSTAGE, artist, updated_at)
            else:
                print("無新發文")
            print("抓取結束")


load_dotenv()

bot = discord.Bot()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Bot is ready to receive commands')
    bstage_bot = BstageBot(bot, Firebase())
    await bstage_bot.execute()


bot.run(os.environ["BOT_TOKEN"])
