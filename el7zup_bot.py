import json
***REMOVED***
from datetime import datetime, timedelta

***REMOVED***quests
from discord import SyncWebhook
from fake_useragent import UserAgent

***REMOVED***_bot
import github
from SnsInfo import SnsInfo, Profile

ua = UserAgent()
user_agent = ua.random
headers = {'user-agent': user_agent}


def convert_to_datetime(date_string):
    # Remove the 'Z' from the string
    return datetime.fromisoformat(date_string[:-1]) + timedelta(hours=0)


# 取得上次最新發文時間
response = github.get_env_variable(github.UPDATED_AT)
if response.ok:
    data = json.loads(response.text)
    updated_at_datetime = convert_to_datetime(data["value"])
    print(f"上次發文時間: {updated_at_datetime}")
    print("開始抓取資料...")
    request = requests.get(headers=headers,
                           url="https://artist.mnetplus.world/svc/stg/el7zup/home/api/v1/home/star?page=1&pageSize=10")
    data = json.loads(request.text)

    sns_info_list = []
    for item in data["feeds"]["items"]:
        published_at_datetime = convert_to_datetime(item["publishedAt"])
        if updated_at_datetime < published_at_datetime:
            sns_info = SnsInfo(post_link=f"https://artist.mnetplus.world/main/stg/el7zup/story/feed/{item['typeId']}",
                               profile=Profile(item["author"]["nickname"], item["author"]["avatarImgPath"]),
                               content=item["description"], images=[image for image in item.get("images", [])],
                               timestamp=published_at_datetime)
            sns_info_list.append(sns_info)
    ***REMOVED***
            break

    post_count = len(sns_info_list)
    if post_count != 0:
        print(f"有 {post_count} 則發文")
        for sns_info in reversed(sns_info_list):
            webhook = SyncWebhook.from_url(os.environ["EL7ZUP_WEBHOOK"])
            webhook.send(embeds=discord_bot.generate_embeds(username="", sns_info=sns_info))
        # 儲存最新發文時間
        updated_at = max([sns_info.timestamp for sns_info in sns_info_list])
        github.set_env_variable(github.UPDATED_AT, updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
***REMOVED***
        print("無新發文")
    print("抓取結束")
