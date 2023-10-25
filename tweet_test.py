import asyncio

***REMOVED***
***REMOVED***_bot
import twitter_graphql_crawler

tweet_url = "https://twitter.com/WeiChe0307/status/1717111716923019352?t=KAj-mDTH8Sozn3oPiE4sFQ&s=19"

# webhook_url = twitter_crawler.get_discord_webhook(tweet_url)
# 測試
webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"
tweet_data = twitter_graphql_crawler.fetch_data(tweet_url)

loop = asyncio.get_event_loop()
loop.run_until_complete(discord_bot.send_message(webhook_url=webhook_url, sns_info=tweet_data))
