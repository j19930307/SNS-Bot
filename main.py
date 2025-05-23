import datetime
import os
import re

import discord
import pytz
from discord import Option, OptionChoice, Embed
from discord.utils import basic_autocomplete
from dotenv import load_dotenv
from google.cloud import firestore

import bstage_crawler
import discord_bot
import instagram_crawler
import threads_crawler
from melon_chart import top100, hot100, daily, weekly, monthly
import twitter_crawler
import weverse_crawler
import youtube_crawler
from discord_bot import (DOMAIN_WEVERSE, DOMAIN_TWITTER, DOMAIN_X,
                         DOMAIN_BSTAGE, DOMAIN_INSTAGRAM, DOMAIN_THREADS)
from firebase import Firebase
from sns_type import SnsType
from urllib.parse import urlparse, urlunparse

from threads_crawler import fetch_data_from_browser

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
firebase = Firebase()
bot = discord.Bot()


async def sns_preview(ctx, url):
    # 取出 domain
    match = re.search(r'https://(www\.)?([^/]+)', url)
    if match:
        domain = match.group(2)
        if domain == DOMAIN_TWITTER or domain == DOMAIN_X:
            pattern = r'(https://' + re.escape(domain) + r'/[^?]+)'
            match = re.search(pattern, url)
            if match:
                tweet_url = match.group(1)
                if tweet_url:
                    print("提取的推文連結:", tweet_url)
                    await ctx.defer()
                    sns_info = twitter_crawler.fetch_data(tweet_url)
                    await discord_bot.send_message(ctx, sns_info)
                else:
                    print("未找到推文連結")
        elif domain == DOMAIN_WEVERSE:
            match = re.search(r'(https://weverse.io/[^?]+)', url)
            if match:
                weverse_url = match.group(0)
                if weverse_url:
                    print("提取的推文連結:", weverse_url)
                    await ctx.defer()
                    sns_info = weverse_crawler.fetch_data(weverse_url)
                    await discord_bot.send_message(ctx, sns_info)
                else:
                    print("未找到推文連結")
        elif domain in DOMAIN_BSTAGE or "story/feed" in url:
            await ctx.defer()
            sns_info = bstage_crawler.fetch_data(url)
            if sns_info:
                await discord_bot.send_message(ctx, sns_info)
            else:
                await ctx.followup.send("資料解析失敗", ephemeral=True)
        elif domain in DOMAIN_INSTAGRAM:
            match = re.search(r'(https://www.instagram.com/(p|reel|stories)/[^?]+)', url)
            if match:
                instagram_url = match.group(0)
                if instagram_url:
                    print("提取的推文連結:", instagram_url)
                    await ctx.defer()
                    sns_info = instagram_crawler.fetch_data_from_graphql(instagram_url)
                    if sns_info:
                        print(sns_info)
                        await discord_bot.send_message(ctx, sns_info)
                    else:
                        await ctx.followup.send(convert_to_instagramez_url(instagram_url))
                else:
                    print("未找到推文連結")
                    await ctx.followup.send("連結格式不符")
        elif domain in DOMAIN_THREADS:
            await ctx.defer()
            sns_info, share_info = threads_crawler.fetch_data_from_browser(url)
            if sns_info:
                await discord_bot.send_message(ctx, sns_info)
                if share_info:
                    await discord_bot.send_message(ctx, share_info)
            else:
                await ctx.followup.send("資料解析失敗", ephemeral=True)
    else:
        print("無法提取域名")


async def read_message(message):
    # 排除機器人本身的訊息，避免無限循環
    # role_mentions.member.id
    if message.author == bot.user:
        return
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
                    sns_info = twitter_crawler.fetch_data(tweet_url)
                    await message.channel.send(content=tweet_url,
                                               embeds=discord_bot.generate_embeds(username, sns_info))
                    if len(sns_info.videos) > 0:
                        await message.channel.send(content="\n".join(sns_info.videos))
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
                                                   embeds=discord_bot.generate_embeds(username,
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
                                                   embeds=discord_bot.generate_embeds(username, sns_info))
                        await loading_message.delete()
                    except:
                        await loading_message.delete()
                else:
                    print("未找到推文連結")
                    await loading_message.delete()
        elif domain in DOMAIN_INSTAGRAM:
            match = re.search(r"https://www.instagram.com/(p|reel|stories)/([^/?]+)", message.content)
            if match:
                instagram_url = f"https://www.instagram.com/{match.group(1)}/{match.group(2)}"
                await message.delete()
                loading_message = await message.channel.send(content="處理中，請稍後...")
                if instagram_url:
                    print("提取的推文連結:", instagram_url)
                    try:
                        sns_info = instagram_crawler.fetch_data_from_graphql(instagram_url)
                        if sns_info:
                            print(sns_info)
                            await message.channel.send(content=instagram_url,
                                                       embeds=discord_bot.generate_embeds(username, sns_info))
                        else:
                            await message.channel.send(convert_to_instagramez_url(instagram_url))
                        await loading_message.delete()
                    except:
                        await loading_message.delete()
                else:
                    print("未找到推文連結")
                    await loading_message.delete()
        else:
            print("無法提取域名")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('Bot is ready to receive commands')


@bot.slash_command(description="輸入網址產生預覽訊息 (支援網站: X, Weverse, Instagram)")
async def preview(ctx, link: Option(str, "請輸入連結", required=True, default='')):
    await sns_preview(ctx, link)


bstage_type = [SnsType.BSTAGE.value, SnsType.MNET_PLUS.value]


@bot.slash_command(description="訂閱 b.stage 帳號通知")
async def bstage_subscribe(ctx, option: Option(str, description="請選擇訂閱平台", choices=bstage_type, required=True),
                           account: Option(str,
                                           "請輸入訂閱帳號，例如 https://h1key.bstage.in，帳號則為 h1key；https://artist.mnetplus.world/main/stg/izna 帳號則為 izna",
                                           required=True, default='')):
    if option == SnsType.BSTAGE.value:
        await add_bstage_account_to_firestore(ctx, SnsType.BSTAGE, account.strip())
    elif option == SnsType.MNET_PLUS.value:
        await add_bstage_account_to_firestore(ctx, SnsType.MNET_PLUS, account.strip())


async def get_subscribed_list_from_firestore(ctx: discord.AutocompleteContext):
    tuple_list = firebase.get_subscribed_list_from_discord_id(SnsType.BSTAGE, str(ctx.interaction.channel.id))
    return [OptionChoice(name=username, value=id) for (username, id) in tuple_list]


@bot.slash_command(description="取消訂閱 b.stage 帳號通知")
async def bstage_unsubscribe(ctx, value: discord.Option(str, "選擇要取消訂閱的帳號",
                                                        autocomplete=basic_autocomplete(
                                                            get_subscribed_list_from_firestore))):
    await remove_account_from_firestore(ctx, SnsType.BSTAGE, value)


@bot.slash_command(description="訂閱 YouTube 頻道影片通知")
async def youtube_subscribe(ctx,
                            account: Option(str,
                                            "請輸入要訂閱頻道的帳號代碼。例如網址為 https://www.youtube.com/@STAYC，代碼則為 STAYC",
                                            required=True, default='')):
    await add_youtube_handle_to_firebase(ctx, account.strip())


async def get_youtube_subscribed_list_from_firestore(ctx: discord.AutocompleteContext):
    channel_list = firebase.get_youtube_subscribed_list_from_discord_id(str(ctx.interaction.channel.id))
    return [OptionChoice(name=id, value=id) for id in channel_list]


@bot.slash_command(description="取消訂閱 YouTube 頻道影片通知")
async def youtube_unsubscribe(ctx, value: discord.Option(str, "選擇要取消訂閱頻道的帳號",
                                                         autocomplete=basic_autocomplete(
                                                             get_youtube_subscribed_list_from_firestore))):
    await remove_account_from_firestore(ctx, SnsType.YOUTUBE, value)


@bot.slash_command(description="時間戳指示符")
async def hammertime(ctx, time: Option(str, "請輸入時間 (格式：年/月/日 時:分:秒)", required=True, default='')):
    await send_hammertime(ctx, time)


chart_type = ["TOP100", "HOT100", "日榜", "周榜", "月榜"]


@bot.slash_command(description="Melon 榜單")
async def melon_chart(ctx, option: Option(str, description="請選擇榜單類型", choices=chart_type, required=True)):
    await ctx.defer()
    if option == "TOP100":
        title, content = await top100()
        await ctx.followup.send(embed=Embed(title=title, description=content))
    elif option == "HOT100":
        title, content = await hot100()
        await ctx.followup.send(embed=Embed(title=title, description=content))
    elif option == "日榜":
        title, content = await daily()
        await ctx.followup.send(embed=Embed(title=title, description=content))
    elif option == "周榜":
        title, content = await weekly()
        await ctx.followup.send(embed=Embed(title=title, description=content))
    elif option == "月榜":
        title, content = await monthly()
        await ctx.followup.send(embed=Embed(title=title, description=content))
    else:
        await ctx.followup.send("請選擇正確的榜單類型")


def convert_to_instagramez_url(link):
    if link.startswith("https://www.instagram.com"):
        parsed_url = urlparse(link)
        # 修改 netloc 來將 'instagram.com' 替換為 'instagramez.com'
        modified_netloc = parsed_url.netloc.replace("instagram.com", "instagramez.com")
        # 使用已修改的 netloc 並移除 query 參數來重建 URL
        modified_url = urlunparse(
            (parsed_url.scheme, modified_netloc, parsed_url.path, parsed_url.params, '', parsed_url.fragment))
        return modified_url


@bot.listen('on_message')
async def on_message(message):
    await read_message(message)


async def remove_account_from_firestore(ctx, sns_type: SnsType, id):
    await ctx.defer()
    firebase.delete_account(sns_type, id)
    await ctx.followup.send("取消訂閱成功")


async def add_bstage_account_to_firestore(ctx, sns_type: SnsType, account: str):
    await ctx.defer()
    if firebase.is_account_exists(sns_type, account):
        await ctx.followup.send(f"{account} 已訂閱過")
    else:
        firebase.add_account(sns_type, id=account, username=account, discord_channel_id=str(ctx.channel.id),
                             updated_at=firestore.SERVER_TIMESTAMP)
        await ctx.followup.send(f"{account} 訂閱成功")


async def add_youtube_handle_to_firebase(ctx, handle: str):
    await ctx.defer()
    if firebase.is_account_exists(SnsType.YOUTUBE, handle):
        await ctx.followup.send(f"{handle} 已訂閱過")
    else:
        channel_name = youtube_crawler.get_channel_name(handle)
        if channel_name is None:
            await ctx.followup.send("頻道不存在")
            return
        videos_id = youtube_crawler.get_latest_videos(handle)
        shorts_id = youtube_crawler.get_latest_shorts(handle)
        streams_id = youtube_crawler.get_latest_streams(handle)
        latest_video_id = videos_id[0] if len(videos_id) > 0 else ""
        latest_short_id = shorts_id[0] if len(shorts_id) > 0 else ""
        latest_stream_id = streams_id[0] if len(streams_id) > 0 else ""
        latest_video_published_at = youtube_crawler.get_video_published_at(video_id=latest_video_id)
        latest_short_published_at = youtube_crawler.get_video_published_at(video_id=latest_short_id)
        latest_stream_published_at = youtube_crawler.get_video_published_at(video_id=latest_stream_id)
        firebase.add_youtube_account(handle=handle, channel_name=channel_name, discord_channel_id=str(ctx.channel.id),
                                     latest_video_id=latest_video_id,
                                     latest_video_published_at=latest_video_published_at,
                                     latest_short_id=latest_short_id,
                                     latest_short_published_at=latest_short_published_at,
                                     latest_stream_id=latest_stream_id,
                                     latest_stream_published_at=latest_stream_published_at)
        await ctx.followup.send(f"{channel_name} 訂閱成功")


# <t:1715925960:d> → 2024/05/17
# <t:1715925960:f> → 2024年5月17日 14:06
# <t:1715925960:t> → 14:06
# <t:1715925960:D> → 2024年5月17日
# <t:1715925960:F> → 2024年5月17日星期五 14:06
# <t:1715925960:R> → 1 天內
# <t:1715925960:T> → 14:06:00
async def send_hammertime(ctx, input: str):
    pattern = r'(\d{4})/(\d{1,2})/(\d{1,2}) ?(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?'
    match = re.match(pattern, input)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4)) if match.group(4) is not None else 0
        minute = int(match.group(5)) if match.group(5) is not None else 0
        second = int(match.group(6)) if match.group(6) is not None else 0
        try:
            tz = pytz.timezone('Asia/Taipei')
            dt = tz.localize(datetime.datetime(year, month, day, hour, minute, second, 0))
            timestamp = str(int(dt.timestamp()))
            embeds = []
            for pair in [(f"<t:{timestamp}:F>", f"\\<t:{timestamp}:F\\>"),
                         (f"<t:{timestamp}:f>", f"\\<t:{timestamp}:f\\>"),
                         (f"<t:{timestamp}:R>", f"\\<t:{timestamp}:R\\>")]:
                embeds.append(Embed(title=pair[0], description=pair[1]))
            await ctx.send_response(embeds=embeds, ephemeral=True)
        except ValueError:
            await ctx.send_response(content="時間格式錯誤", ephemeral=True)
    else:
        await ctx.send_response(content="時間格式錯誤", ephemeral=True)


bot.run(BOT_TOKEN)
