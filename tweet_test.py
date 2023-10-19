***REMOVED***
***REMOVED***_bot

tweet_url = "https://twitter.com/STAYC_official/status/1714567494021833103"

webhook_url = twitter_crawler.get_discord_webhook(tweet_url)
# 測試
# webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"
tweet_data = twitter_crawler.fetch_data_from_tweet(tweet_url)

discord_bot.send_message(webhook_url=webhook_url, sns_info=tweet_data)
