"""
實用工具指令模組
包含預覽連結、時間戳等功能
"""
import datetime
import re

import pytz
from discord import Option, Embed, ApplicationContext, Attachment, AutocompleteContext

from services.preview_service import PreviewService

# ── 成員資料 ────────────────────────────────────────────────────────────────

# 成員名單（順序對應 S{index}.jpg 圖片編號）
MEMBERS = [
    "SeoYeon", "HyeRin", "JiWoo", "ChaeYeon", "YooYeon", "SooMin",
    "NaKyoung", "YuBin", "Kaede", "DaHyun", "Kotone", "YeonJi",
    "Nien", "SoHyun", "Xinyu", "Mayu", "Lynn", "JooBin",
    "HaYeon", "ShiOn", "ChaeWon", "Sullin", "SeoAh", "JiYeon"
]

COSMO_ICON_URL = (
    "https://play-lh.googleusercontent.com/"
    "nUqYDQQ-FlmKxnwBgxMhUVTO_tLpvIzLS8NMP9Xjw-"
    "mbHRCgEHAUsa8xQ9G8ujMR9w"
)
MEMBER_PROFILE_BASE_URL = "https://static.cosmo.fans/uploads/member-profile/2025-05-01"


# ── 自動補完 ────────────────────────────────────────────────────────────────

async def get_member_names(ctx: AutocompleteContext) -> list[str]:
    """
    Slash Command 自動補完：根據使用者輸入過濾成員名單。
    ctx.value 為使用者目前輸入的文字。
    """
    if not ctx.value:
        return MEMBERS[:24]  # 未輸入時預設顯示前 24 名

    # 不分大小寫比對
    return [name for name in MEMBERS if ctx.value.lower() in name.lower()]


# ── 指令設定 ────────────────────────────────────────────────────────────────

def setup_utility_commands(bot):
    """設定實用工具指令"""

    preview_service = PreviewService(bot)

    @bot.slash_command(description="輸入網址產生預覽訊息 (支援網站: X, Weverse, Instagram)")
    async def preview(
            ctx,
            link: Option(str, "請輸入連結", required=True),
            show_all: Option(bool, "顯示所有圖片和影片", default=False)
    ):
        await preview_service.generate_preview(ctx, link, show_all)

    @bot.slash_command(description="時間戳指示符")
    async def hammertime(
            ctx,
            time: Option(str, "請輸入時間 (格式：年/月/日 時:分:秒)", required=True)
    ):
        await _generate_hammertime(ctx, time)

    @bot.slash_command(description="建立 COSMO Room 貼文")
    async def create_cosmo_room(
            ctx: ApplicationContext,
            member: Option(str, description="請選擇成員", autocomplete=get_member_names, required=True),
            description: Option(str, description="內容描述", required=False),
            image1: Option(Attachment, description="第一張圖片", required=False),
            image2: Option(Attachment, description="第二張圖片", required=False),
            image3: Option(Attachment, description="第三張圖片", required=False),
            image4: Option(Attachment, description="第四張圖片", required=False)
    ):
        # 驗證第一張圖片的檔案類型（必填驗證在邏輯層處理）
        if image1 and not image1.content_type.startswith("image/"):
            await ctx.respond("這不是有效的圖片檔案！", ephemeral=True)
            return

        # 收集所有有效的圖片附件
        attachments = [img for img in (image1, image2, image3, image4) if img is not None]

        # 建立並回覆 Embed 列表
        embeds = _build_cosmo_embeds(member, description, attachments)
        await ctx.respond(embeds=embeds)


# ── 內部輔助函式 ────────────────────────────────────────────────────────────

def _build_cosmo_embeds(
        member: str,
        description: str | None,
        attachments: list[Attachment]
) -> list[Embed]:
    """
    為指定成員與圖片附件建立 Discord Embed 列表。

    Discord 的多圖片群組規則：
    - 所有 Embed 必須使用相同的 `url`，才會被合併顯示。
    - 第一個 Embed 承載標題、描述與作者資訊，其餘只設圖片。
    """
    # S 編號從 1 開始（index + 1）
    member_index = MEMBERS.index(member) + 1
    member_image_url = f"{MEMBER_PROFILE_BASE_URL}/S{member_index}.jpg"

    # 第一個 Embed 一定存在，包含作者與 footer
    first_embed = Embed(description=description, url=member_image_url)
    first_embed.set_author(name=member, icon_url=member_image_url)
    first_embed.set_footer(text="COSMO", icon_url=COSMO_ICON_URL)

    # 若有第一張圖片就附上，否則 Embed 僅含文字資訊
    if attachments:
        first_embed.set_image(url=attachments[0].url)

    embeds = [first_embed]

    # 第二張圖片之後，每張各建一個 Embed（需相同 url 才能群組顯示）
    for attachment in attachments[1:]:
        embed = Embed(url=member_image_url)
        embed.set_image(url=attachment.url)
        embeds.append(embed)

    return embeds


async def _generate_hammertime(ctx, input_time: str):
    """產生 Discord 時間戳格式的回覆"""
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
        dt = tz.localize(datetime.datetime(year, month, day, hour, minute, second))
        timestamp = str(int(dt.timestamp()))

        # 產生三種常用的 Discord 時間戳格式
        timestamp_formats = [
            (f"<t:{timestamp}:F>", f"\\<t:{timestamp}:F\\>"),  # 完整日期時間
            (f"<t:{timestamp}:f>", f"\\<t:{timestamp}:f\\>"),  # 簡短日期時間
            (f"<t:{timestamp}:R>", f"\\<t:{timestamp}:R\\>"),  # 相對時間
        ]

        embeds = [
            Embed(title=display, description=code)
            for display, code in timestamp_formats
        ]

        await ctx.send_response(embeds=embeds, ephemeral=True)

    except ValueError:
        await ctx.send_response(content="時間格式錯誤", ephemeral=True)
