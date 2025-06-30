"""
榜單指令模組
處理 Melon 音樂榜單查詢
"""
from discord import Option, Embed
from melon_chart import top100, hot100, daily, weekly, monthly


def setup_chart_commands(bot):
    """設定榜單指令"""

    chart_type = ["TOP100", "HOT100", "日榜", "周榜", "月榜"]

    @bot.slash_command(description="Melon 榜單")
    async def melon_chart(ctx, option: Option(str, description="請選擇榜單類型", choices=chart_type, required=True)):
        await _handle_melon_chart(ctx, option)


async def _handle_melon_chart(ctx, chart_option: str):
    """處理 Melon 榜單查詢"""
    await ctx.defer()

    chart_handlers = {
        "TOP100": top100,
        "HOT100": hot100,
        "日榜": daily,
        "周榜": weekly,
        "月榜": monthly
    }

    handler = chart_handlers.get(chart_option)
    if handler:
        try:
            title, content = await handler()
            await ctx.followup.send(embed=Embed(title=title, description=content))
        except Exception as e:
            await ctx.followup.send(f"取得榜單時發生錯誤: {str(e)}")
    else:
        await ctx.followup.send("請選擇正確的榜單類型")