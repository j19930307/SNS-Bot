"""
訊息處理器
負責處理自動連結預覽功能
"""
import re
import discord

from services.preview_service import PreviewService
from utils.url_utils import extract_domain


class MessageHandler:
    """訊息處理器類別"""

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.preview_service = PreviewService(bot)

    async def handle_message(self, message):
        """處理訊息"""
        # 排除機器人本身的訊息，避免無限循環
        if message.author == self.bot.user:
            return

        # 檢查訊息中是否包含支援的社群媒體連結
        if self._contains_supported_url(message.content):
            await self._process_social_media_link(message)

    def _contains_supported_url(self, content: str) -> bool:
        """檢查內容是否包含支援的社群媒體連結"""
        supported_domains = [
            'twitter.com', 'x.com', 'weverse.io', 'instagram.com',
            'threads.com', 'berriz.in'
        ]

        bstage_domains = [
            'h1key-official.com', 'h1key.bstage.in', 'yeeun.bstage.in',
            'purplekiss.co.kr', 'kissoflife-official.com', 'kissoflife.bstage.in'
        ]

        all_domains = supported_domains + bstage_domains

        for domain in all_domains:
            if domain in content:
                return True

        return False

    async def _process_social_media_link(self, message):
        """處理社群媒體連結"""
        username = message.author.nick
        domain = extract_domain(message.content)

        if not domain:
            return

        # 刪除原始訊息並顯示處理中訊息
        await message.delete()
        loading_message = await message.channel.send(content="處理中，請稍後...")

        try:
            # 根據不同平台處理連結
            success = await self._handle_platform_link(message, username, domain)

            if not success:
                print(f"無法處理 {domain} 的連結")

        except Exception as e:
            print(f"處理連結時發生錯誤: {e}")
        finally:
            # 刪除處理中訊息
            await loading_message.delete()

    async def _handle_platform_link(self, message, username: str, domain: str) -> bool:
        """根據平台處理連結"""
        content = message.content

        if domain in ['twitter.com', 'x.com']:
            return await self._handle_twitter_link(message, username, content, domain)
        elif domain == 'weverse.io':
            return await self._handle_weverse_link(message, username, content)
        elif domain == 'instagram.com':
            return await self._handle_instagram_link(message, username, content)
        elif self._is_bstage_domain(domain):
            return await self._handle_bstage_link(message, username, content, domain)

        return False

    def _is_bstage_domain(self, domain: str) -> bool:
        """檢查是否為 B.stage 相關域名"""
        bstage_domains = [
            'h1key-official.com', 'h1key.bstage.in', 'yeeun.bstage.in',
            'purplekiss.co.kr', 'kissoflife-official.com', 'kissoflife.bstage.in'
        ]
        return domain in bstage_domains

    async def _handle_twitter_link(self, message, username: str, content: str, domain: str) -> bool:
        """處理 Twitter/X 連結"""
        pattern = r'(https://' + re.escape(domain) + r'/[^?]+)'
        match = re.search(pattern, content)

        if match:
            tweet_url = match.group(1)
            print(f"提取的推文連結: {tweet_url}")

            import twitter_crawler
            import discord_bot

            sns_info = twitter_crawler.fetch_data(tweet_url)
            await message.channel.send(
                content=tweet_url,
                embeds=discord_bot.generate_embeds(username, sns_info)
            )

            if len(sns_info.videos) > 0:
                await message.channel.send(content="\n".join(sns_info.videos))

            return True

        return False

    async def _handle_weverse_link(self, message, username: str, content: str) -> bool:
        """處理 Weverse 連結"""
        match = re.search(r'(https://weverse.io/[^?]+)', content)

        if match:
            weverse_url = match.group(0)
            print(f"提取的 Weverse 連結: {weverse_url}")

            try:
                import weverse_crawler
                import discord_bot

                sns_info = weverse_crawler.fetch_data(weverse_url)
                await message.channel.send(
                    content=weverse_url,
                    embeds=discord_bot.generate_embeds(username, sns_info)
                )
                return True
            except Exception as e:
                print(f"處理 Weverse 連結時發生錯誤: {e}")

        return False

    async def _handle_instagram_link(self, message, username: str, content: str) -> bool:
        """處理 Instagram 連結"""
        from utils.url_utils import convert_to_instagramez_url

        match = re.search(r"https://www.instagram.com/(p|reel|stories)/([^/?]+)", content)

        if match:
            instagram_url = f"https://www.instagram.com/{match.group(1)}/{match.group(2)}"
            print(f"提取的 Instagram 連結: {instagram_url}")

            try:
                import instagram_crawler
                import discord_bot

                sns_info = instagram_crawler.fetch_data_from_graphql(instagram_url)

                if sns_info:
                    await message.channel.send(
                        content=instagram_url,
                        embeds=discord_bot.generate_embeds(username, sns_info)
                    )
                else:
                    await message.channel.send(convert_to_instagramez_url(instagram_url))

                return True
            except Exception as e:
                print(f"處理 Instagram 連結時發生錯誤: {e}")

        return False

    async def _handle_bstage_link(self, message, username: str, content: str, domain: str) -> bool:
        """處理 B.stage 連結"""
        pattern = r'(https://' + re.escape(domain) + r'/(story/feed/[^?]+|contents/[^?]+))'
        match = re.search(pattern, content)

        if match:
            bstage_url = match.group(1)
            print(f"提取的 B.stage 連結: {bstage_url}")

            try:
                import bstage_crawler
                import discord_bot

                sns_info = bstage_crawler.fetch_data(bstage_url)

                content_list = [bstage_url]
                if sns_info.videos:
                    content_list.extend(sns_info.videos)

                await message.channel.send(
                    content="\n".join(content_list),
                    embeds=discord_bot.generate_embeds(username, sns_info)
                )
                return True
            except Exception as e:
                print(f"處理 B.stage 連結時發生錯誤: {e}")

        return False