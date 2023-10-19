***REMOVED***_bot
***REMOVED***

fetch_url = "https://weverse.io/lightsum/artist/3-137284105"

webhook_url = weverse_crawler.get_discord_webhook(fetch_url)

# 測試
# webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"
data = weverse_crawler.fetch_data_from_weverse(fetch_url)

discord_bot.send_message(webhook_url=webhook_url, sns_info=data)
