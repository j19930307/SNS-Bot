"""
實用工具指令模組
包含預覽連結、時間戳等功能
"""
import re
import datetime
import pytz
from discord import Option, Embed

from services.preview_service import PreviewService


def setup_utility_commands(bot):
    """設定實用工具指令"""

    preview_service = PreviewService(bot)

    @bot.slash_command(description="輸入網址產生預覽訊息 (支援網站: X, Weverse, Instagram)")
    async def preview(ctx, link: Option(str, "請輸入連結", required=True)):
        await preview_service.generate_preview(ctx, link)

    @bot.slash_command(description="時間戳指示符")
    async def hammertime(ctx, time: Option(str, "請輸入時間 (格式：年/月/日 時:分:秒)", required=True)):
        await _generate_hammertime(ctx, time)


async def _generate_hammertime(ctx, input_time: str):
    """產生 Discord 時間戳"""
    pattern = r'(\d{4})/(\d{1,2})/(\d{1,2}) ?(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?'
    match = re.match(pattern, input_time)

    if not match:
        await ctx.send_response(content="時間格式錯誤", ephemeral=True)
        return

    try:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4)) if match.group(4) else 0
        minute = int(match.group(5)) if match.group(5) else 0
        second = int(match.group(6)) if match.group(6) else 0

        tz = pytz.timezone('Asia/Taipei')
        dt = tz.localize(datetime.datetime(year, month, day, hour, minute, second, 0))
        timestamp = str(int(dt.timestamp()))

        embeds = []
        timestamp_formats = [
            (f"<t:{timestamp}:F>", f"\\<t:{timestamp}:F\\>"),
            (f"<t:{timestamp}:f>", f"\\<t:{timestamp}:f\\>"),
            (f"<t:{timestamp}:R>", f"\\<t:{timestamp}:R\\>")
        ]

        for display, code in timestamp_formats:
            embeds.append(Embed(title=display, description=code))

        await ctx.send_response(embeds=embeds, ephemeral=True)

    except ValueError:
        await ctx.send_response(content="時間格式錯誤", ephemeral=True)