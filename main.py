"""
Discord Bot 主程式
負責初始化 Bot 並載入各種指令模組
"""
import os

import discord
from dotenv import load_dotenv
from sns_core.clients import FirestoreSubscriptionStore
from sns_core.utils import decode_base64_json

from commands.chart_commands import setup_chart_commands
from commands.subscription_commands import setup_subscription_commands
from commands.utility_commands import setup_utility_commands

# 載入環境變數
load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
firebase_admin_key = os.getenv("FIREBASE_ADMIN_KEY")
if not firebase_admin_key:
    raise ValueError("環境變數中找不到 FIREBASE_ADMIN_KEY！")

# 初始化 Firebase 和 Bot
firebase = FirestoreSubscriptionStore(decode_base64_json(firebase_admin_key))
bot = discord.Bot()


@bot.event
async def on_ready():
    """Bot 準備就緒事件"""
    print(f'已登入為 {bot.user.name} ({bot.user.id})')
    print('Bot 準備就緒，可以接收指令')


# --- 定義帶有權限檢查的確認按鈕 View ---
class DeleteConfirmView(discord.ui.View):
    def __init__(self, target_msg, command_msg, confirmation_msg_placeholder=None):
        super().__init__(timeout=30)
        self.target_msg = target_msg
        self.command_msg = command_msg
        # 用來存儲「確認訊息」本身，以便超時後編輯它
        self.confirmation_msg = None

    async def on_timeout(self):
        """
        當 30 秒內沒有任何互動時，會自動執行這個函式。
        """
        if self.confirmation_msg:
            try:
                # 做法 A：直接刪除這條確認訊息 (推薦，最乾淨)
                await self.confirmation_msg.delete()
            except discord.NotFound:
                pass # 訊息可能已經被手動刪除或點擊刪除了

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        這是一個內建過濾器，會檢查點擊按鈕的人是否為指令發送者。
        """
        if interaction.user.id != self.command_msg.author.id:
            # ephemeral=True 代表只有點錯的人看得到這則警告，不影響頻道內容
            await interaction.response.send_message(
                f"❌ 只有 {self.command_msg.author.display_name} 才能操作這個選單！",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="確認刪除", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_callback(self, button, interaction):
        try:
            # 1. 刪除目標訊息 (機器人發的那則)
            await self.target_msg.delete()
            # 2. 刪除使用者的指令訊息 (那個 @機器人 刪除 的訊息)
            await self.command_msg.delete()
            # 3. 修改當前的確認選單訊息，告知成功並在 3 秒後自動消失
            await interaction.response.edit_message(
                content="✅ 訊息已成功刪除，本提示將自動關閉。",
                view=None,
                delete_after=3
            )
        except discord.NotFound:
            await interaction.response.edit_message(content="❌ 找不到目標訊息，可能已被手動刪除。", view=None)

    @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)
    async def cancel_callback(self, button, interaction):
        # 取消後直接移除按鈕並在 3 秒後刪除提示
        await interaction.response.edit_message(content="已取消刪除動作。", view=None, delete_after=3)


# --- 主程式 on_message ---
@bot.event
async def on_message(message: discord.Message):
    # 基礎過濾：忽略機器人、檢查是否提到機器人、檢查關鍵字
    if message.author.bot:
        return

    is_mention = bot.user in message.mentions
    # 移除 Mention 字串後檢查內容
    clean_content = message.content.replace(f'<@{bot.user.id}>', '').strip().lower()
    is_delete_command = clean_content in ["delete"]

    if not (is_mention and is_delete_command):
        return

    # 檢查是否有 Reply (引用)
    if message.reference is None:
        await message.reply("💡 請 **Reply (回覆)** 你想刪除的那則機器人訊息，並輸入「刪除」。", mention_author=False)
        return

    try:
        # 獲取被引用的目標訊息
        target = await message.channel.fetch_message(message.reference.message_id)
    except discord.NotFound:
        await message.reply("找不到該訊息，可能已被刪除。", mention_author=False)
        return

    # 權限檢查：只能刪除機器人自己的訊息
    if target.author.id != bot.user.id:
        await message.reply("🚫 我只能刪除由我發送的訊息喔！", mention_author=False)
        return

    # 啟動防呆 View
    view = DeleteConfirmView(target_msg=target, command_msg=message)
    # 先發送訊息，並將回傳的訊息物件存入 view 中
    conf_msg = await message.reply("⚠️ 你確定要刪除這則訊息嗎？", view=view, mention_author=False)
    view.confirmation_msg = conf_msg  # 告訴 view 它是哪一條訊息，超時好去處理它


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
