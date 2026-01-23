"""
預覽服務
負責處理各種社群媒體連結的預覽功能
"""
import re

import discord

import discord_bot
from utils.url_utils import extract_domain, convert_to_custom_instagram_url, shorten_url


class PreviewService:
    """預覽服務類別"""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    async def generate_preview(self, ctx, url: str):
        """產生連結預覽"""
        domain = extract_domain(url)

        if not domain:
            await ctx.followup.send("無法識別的連結格式", ephemeral=True)
            return

        await ctx.defer()

        try:
            if domain in ['twitter.com', 'x.com']:
                await self._preview_twitter(ctx, url, domain)
            elif domain == 'weverse.io':
                await self._preview_weverse(ctx, url)
            elif domain == 'instagram.com':
                await self._preview_instagram(ctx, url)
            elif domain == 'threads.com':
                await self._preview_threads(ctx, url)
            elif domain == 'link.berriz.in':
                await self._preview_berriz(ctx, url)
            elif "story/feed" in url:
                await self._preview_bstage(ctx, url)
            else:
                await ctx.followup.send("不支援的網站", ephemeral=True)

        except Exception as e:
            await ctx.followup.send(f"預覽生成失敗: {str(e)}", ephemeral=True)

    async def _preview_twitter(self, ctx, url: str, domain: str):
        """預覽 Twitter/X 內容"""
        pattern = r'(https://' + re.escape(domain) + r'/[^?]+)'
        match = re.search(pattern, url)

        if match:
            tweet_url = match.group(1)
            print(f"提取的推文連結: {tweet_url}")

            import twitter_crawler
            sns_info = twitter_crawler.fetch_data(tweet_url)
            await self._send_preview(ctx, sns_info)

    async def _preview_weverse(self, ctx, url: str):
        """預覽 Weverse 內容"""
        match = re.search(r'(https://weverse.io/[^?]+)', url)

        if match:
            weverse_url = match.group(0)
            print(f"提取的 Weverse 連結: {weverse_url}")

            import weverse_crawler
            sns_info = weverse_crawler.fetch_data(weverse_url)
            await self._send_preview(ctx, sns_info)

    async def _preview_instagram(self, ctx, url: str):
        """預覽 Instagram 內容"""
        match = re.search(r'(https://www.instagram.com/(p|reel|reels|stories)/[^?]+)', url)

        if match:
            instagram_url = match.group(0)
            print(f"提取的 Instagram 連結: {instagram_url}")

            import instagram_crawler
            sns_info = instagram_crawler.fetch_data_from_graphql(instagram_url)

            if sns_info:
                print(sns_info)
                await self._send_preview(ctx, sns_info)
            else:
                await ctx.followup.send(convert_to_custom_instagram_url(instagram_url))

    async def _preview_threads(self, ctx, url: str):
        """預覽 Threads 內容"""
        import threads_crawler
        sns_info, share_info = await threads_crawler.fetch_data_from_browser(url)

        if sns_info:
            await self._send_preview(ctx, sns_info)
            if share_info:
                await self._send_preview(ctx, share_info)
        else:
            await ctx.followup.send("資料解析失敗", ephemeral=True)

    async def _preview_berriz(self, ctx, url: str):
        """預覽 Berriz 內容"""
        import berriz_crawler
        sns_info = berriz_crawler.fetch_data(url)

        if sns_info:
            await self._send_preview(ctx, sns_info)
        else:
            await ctx.followup.send("抓取資料失敗", ephemeral=True)

    async def _preview_bstage(self, ctx, url: str):
        """預覽 B.stage 內容"""
        import bstage_crawler
        sns_info = bstage_crawler.fetch_data(url)

        if sns_info:
            await self._send_preview(ctx, sns_info)
        else:
            await ctx.followup.send("資料解析失敗", ephemeral=True)

    async def _send_preview(self, ctx, sns_info):
        """發送預覽訊息"""
        print(f"訊息內容:\n{sns_info}")
        await ctx.followup.send(sns_info.post_link, embeds=discord_bot.generate_embeds(sns_info))

        videos = [
            shorten_url(video) if len(video) > 100 else video
            for video in (sns_info.videos or [])
        ]

        if videos:
            await ctx.followup.send(content="\n".join(videos))
