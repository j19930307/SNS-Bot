"""
Discord Bot 主程式
負責初始化 Bot 並載入各種指令模組
"""
import os
from dotenv import load_dotenv
import discord

from commands.subscription_commands import setup_subscription_commands
from commands.utility_commands import setup_utility_commands
from commands.chart_commands import setup_chart_commands
from firebase import Firebase

# 載入環境變數
load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]

# 初始化 Firebase 和 Bot
firebase = Firebase()
bot = discord.Bot()


@bot.event
async def on_ready():
    """Bot 準備就緒事件"""
    print(f'已登入為 {bot.user.name} ({bot.user.id})')
    print('Bot 準備就緒，可以接收指令')


def main():
    """主函式"""
    # 設定各種指令
    setup_subscription_commands(bot, firebase)
    setup_utility_commands(bot)
    setup_chart_commands(bot)

    # 啟動 Bot
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    main()