import asyncio

***REMOVED***_bot
***REMOVED***

fetch_url = "https://weverse.io/wooah/artist/4-137746729"

webhook_url = weverse_crawler.get_discord_webhook("_EL7ZUPofficial")

# 測試
# webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"
data = weverse_crawler.fetch_data_from_weverse(fetch_url)

# https://weverse.io/stayc/artist/2-128346763
# https://weverse.io/stayc/artist/3-137359149
# https://weverse.io/stayc/artist/3-137376228

loop = asyncio.get_event_loop()
loop.run_until_complete(discord_bot.send_message(webhook_url=webhook_url, sns_info=data))
