"""
訂閱相關指令模組
包含 B.stage 和 YouTube 的訂閱/取消訂閱功能
"""
import discord
from discord import Option, OptionChoice
from discord.utils import basic_autocomplete
from google.cloud import firestore

from sns_type import SnsType
import youtube_crawler


def setup_subscription_commands(bot: discord.Bot, firebase):
    """設定訂閱相關指令"""

    # B.stage 相關指令
    bstage_type = [SnsType.BSTAGE.value, SnsType.MNET_PLUS.value]

    @bot.slash_command(description="訂閱 B.stage 帳號通知")
    async def bstage_subscribe(
            ctx,
            option: Option(str, description="請選擇訂閱平台", choices=bstage_type, required=True),
            account: Option(str,
                            "請輸入訂閱帳號，例如 https://h1key.bstage.in，帳號則為 h1key；https://artist.mnetplus.world/main/stg/izna 帳號則為 izna",
                            required=True, default='')
    ):
        if option == SnsType.BSTAGE.value:
            await _add_bstage_account(ctx, firebase, SnsType.BSTAGE, account.strip())
        elif option == SnsType.MNET_PLUS.value:
            await _add_bstage_account(ctx, firebase, SnsType.MNET_PLUS, account.strip())

    async def _get_bstage_subscribed_list(ctx: discord.AutocompleteContext):
        """取得 B.stage 訂閱清單（自動完成用）"""
        tuple_list = firebase.get_subscribed_list_from_discord_id(SnsType.BSTAGE, str(ctx.interaction.channel.id))
        return [OptionChoice(name=username, value=id) for (username, id) in tuple_list]

    @bot.slash_command(description="取消訂閱 B.stage 帳號通知")
    async def bstage_unsubscribe(
            ctx,
            value: discord.Option(str, "選擇要取消訂閱的帳號",
                                  autocomplete=basic_autocomplete(_get_bstage_subscribed_list))
    ):
        await _remove_account(ctx, firebase, SnsType.BSTAGE, value)

    # YouTube 相關指令
    @bot.slash_command(description="訂閱 YouTube 頻道影片通知")
    async def youtube_subscribe(
            ctx,
            account: Option(str, "請輸入要訂閱頻道的帳號代碼。例如網址為 https://www.youtube.com/@STAYC，代碼則為 STAYC",
                            required=True, default='')
    ):
        await _add_youtube_account(ctx, firebase, account.strip())

    async def _get_youtube_subscribed_list(ctx: discord.AutocompleteContext):
        """取得 YouTube 訂閱清單（自動完成用）"""
        channel_list = firebase.get_youtube_subscribed_list_from_discord_id(str(ctx.interaction.channel.id))
        return [OptionChoice(name=id, value=id) for id in channel_list]

    @bot.slash_command(description="取消訂閱 YouTube 頻道影片通知")
    async def youtube_unsubscribe(
            ctx,
            value: discord.Option(str, "選擇要取消訂閱頻道的帳號",
                                  autocomplete=basic_autocomplete(_get_youtube_subscribed_list))
    ):
        await _remove_account(ctx, firebase, SnsType.YOUTUBE, value)


async def _add_bstage_account(ctx, firebase, sns_type: SnsType, account: str):
    """新增 B.stage 帳號訂閱"""
    await ctx.defer()
    if firebase.is_account_exists(sns_type, account):
        await ctx.followup.send(f"{account} 已訂閱過")
    else:
        firebase.add_account(
            sns_type,
            id=account,
            username=account,
            discord_channel_id=str(ctx.channel.id),
            updated_at=firestore.SERVER_TIMESTAMP
        )
        await ctx.followup.send(f"{account} 訂閱成功")


async def _add_youtube_account(ctx, firebase, handle: str):
    """新增 YouTube 頻道訂閱"""
    await ctx.defer()
    if firebase.is_account_exists(SnsType.YOUTUBE, handle):
        await ctx.followup.send(f"{handle} 已訂閱過")
    else:
        channel_name = youtube_crawler.get_channel_name(handle)
        if channel_name is None:
            await ctx.followup.send("頻道不存在")
            return

        # 取得最新影片資訊
        videos_id = youtube_crawler.get_latest_videos(handle)
        shorts_id = youtube_crawler.get_latest_shorts(handle)
        streams_id = youtube_crawler.get_latest_streams(handle)

        latest_video_id = videos_id[0] if len(videos_id) > 0 else ""
        latest_short_id = shorts_id[0] if len(shorts_id) > 0 else ""
        latest_stream_id = streams_id[0] if len(streams_id) > 0 else ""

        latest_video_published_at = youtube_crawler.get_video_published_at(video_id=latest_video_id)
        latest_short_published_at = youtube_crawler.get_video_published_at(video_id=latest_short_id)
        latest_stream_published_at = youtube_crawler.get_video_published_at(video_id=latest_stream_id)

        firebase.add_youtube_account(
            handle=handle,
            channel_name=channel_name,
            discord_channel_id=str(ctx.channel.id),
            latest_video_id=latest_video_id,
            latest_video_published_at=latest_video_published_at,
            latest_short_id=latest_short_id,
            latest_short_published_at=latest_short_published_at,
            latest_stream_id=latest_stream_id,
            latest_stream_published_at=latest_stream_published_at
        )
        await ctx.followup.send(f"{channel_name} 訂閱成功")


async def _remove_account(ctx, firebase, sns_type: SnsType, id):
    """移除帳號訂閱"""
    await ctx.defer()
    firebase.delete_account(sns_type, id)
    await ctx.followup.send("取消訂閱成功")