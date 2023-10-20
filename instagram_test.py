import instagram_crawler
***REMOVED***_bot

url = "https://www.instagram.com/p/CynPhAMJpz0"

# 測試
# webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"
data = instagram_crawler.fetch_data_from_instagram(url)
webhook_url = instagram_crawler.get_discord_webhook(data[0])

discord_bot.send_message(webhook_url=webhook_url, sns_info=data[1])
