***REMOVED***
***REMOVED***_bot

tweet_url = "https://twitter.com/STAYC_talk/status/1713921285229855051"

webhook_url = twitter_crawler.get_discord_webhook(tweet_url)
# 測試
# webhook_url = "https://discord.com/api/webhooks/1162632449545752597/sCvieQPZNw5G9XX1iPS-N3WusXnPfrcUU3YjPHlnBzI_CepxO7t4jGKFlRVFDvJNVhNc"
tweet_profile = twitter_crawler.get_profile_from_tweet(tweet_url)
tweet_data = twitter_crawler.fetch_data_from_tweet(tweet_url)

discord_bot.send_message(webhook_url=webhook_url, link=tweet_url, profile_name=tweet_profile[0],
                         profile_image_url=tweet_profile[1],
                         content=tweet_data[0], images=tweet_data[1])
