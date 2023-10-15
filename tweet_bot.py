import tweepy

# 替换为你的API密钥和访问令牌
consumer_key = 'emA34wWIoXaRq1ECGKWecOsPS'
consumer_secret = 'EnthYXZd9plvdYLkuaHFtR5uqfiThSjZNiIw79tqbjJWhwO2oL'
access_token = '885480602073407491-hipcRxVCeOJt85Gj6I4wpE6QA0vBFCy'
access_token_secret = 'yg8X8K7EKDCuowOgsKplbwClvc2paQvgFgXcnQiFPWm1Z'
bearer_token = "AAAAAAAAAAAAAAAAAAAAAAEMqgEAAAAAwaOx8cciP58kJ1JaBcANQc54Lyg%3D9fmDWbPpFaugqM2bnFlZytUOcTNHSMDNdjBg2uETvX3isVcY2o"

# # 设置API凭据
# auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
# auth.set_access_token(access_token, access_token_secret)

# 创建Tweepy客户端
client = tweepy.Client(bearer_token=bearer_token, consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_token,access_token_secret=access_token_secret)

# 获取特定帐户的用户信息
user = client.get_users_tweets(id='1379258225288048640')

# 获取该用户的最新推文
# tweets = client.user_timeline(screen_name=user.screen_name, count=10)  # 限制获取推文的数量

# 打印最新推文
for tweet in user:
    print(f'{tweet.user.screen_name}: {tweet.text}')


