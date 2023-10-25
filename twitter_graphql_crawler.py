***REMOVED***

***REMOVED***quests
import json

from SnsInfo import SnsInfo, Profile


def fetch_data(url: str):
    tweet_id = find_tweet_id(url)
    if tweet_id is None:
***REMOVED***

    api = requests.get(
        "https://raw.githubusercontent.com/fa0311/TwitterInternalAPIDocument/v1.2/docs/json/API.json"
    ).json()

    # Always use new APIs
    # api = requests.get("https://github.com/fa0311/TwitterInternalAPIDocument/blob/master/docs/json/API.json").json()

    headers = api["header"]
    session = requests.session()
    session.get(
        "https://developer.twitter.com", headers={"User-Agent": headers["User-Agent"]}
    )
    x_guest_token = session.post(
        "https://api.twitter.com/1.1/guest/activate.json", headers=headers
    ).json()["guest_token"]

    # <Recommendation> You can also use TwitterFrontendFlow
    # flow = TwitterFrontendFlow()
    # session = flow.session
    # x_guest_token = flow.x_guest_token

    headers.update(
        {
            "Content-type": "application/json",
            "x-guest-token": x_guest_token,
            "x-csrf-token": session.cookies.get("ct0"),
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "en",
        }
    )

    # API you want to use
    operationName = "TweetResultByRestId"

    # variables must be entered by yourself
    variables = {
        "tweetId": f"{tweet_id}",
        "withCommunity": False,
        "includePromotedContent": False,
        "withVoice": False,
    }

    features = {
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": False,
        "tweet_awards_web_tipping_enabled": False,
        "responsive_web_home_pinned_timelines_enabled": True,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "responsive_web_media_download_video_enabled": False,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_enhance_cards_enabled": False
    }

    data = api["graphql"][operationName]
    parameters = {
        "queryId": data["queryId"],
        "variables": json.dumps(variables),
        "features": json.dumps(features),
    }

    data["url"] = "https://api.twitter.com/graphql/5GOHgZe-8U2j5sVHQzEm9A/TweetResultByRestId"

    if data["method"] == "GET":
        response = session.get(data["url"], headers=headers, params=parameters).json()
***REMOVED*** combine_sns_info(url, response)
    # elif data["method"] == "POST":
    #     response = session.post(data["url"], headers=headers, json=parameters).json()


# 找出 tweet id
def find_tweet_id(url: str):
    tweet_id_match = re.search(r'/status/(\d+)', url)
    if tweet_id_match:
***REMOVED*** tweet_id_match.group(1)
***REMOVED***
        print("未找到推文ID")
***REMOVED*** None


def combine_sns_info(post_link: str, response):
    username = response["data"]["tweetResult"]["result"]["core"]["user_results"]["result"]["legacy"]["name"]
    userid = response["data"]["tweetResult"]["result"]["core"]["user_results"]["result"]["legacy"]["screen_name"]
    user_image_url = response["data"]["tweetResult"]["result"]["core"]["user_results"]["result"]["legacy"][
        "profile_image_url_https"]
    post_content = response["data"]["tweetResult"]["result"]["legacy"]["full_text"]
    image_or_video_list = []
    for media in response["data"]["tweetResult"]["result"]["legacy"]["extended_entities"]["media"]:
        if media["type"] == "video" or media["type"] == "animated_gif":
            # 使用max()函数找出bitrate最大的URL
            video_url = max(media["video_info"]["variants"], key=lambda x: x.get('bitrate', 0))["url"]
            image_or_video_list.append(video_url)
        elif media["type"] == "photo":
            image = media["media_url_https"]
            image_or_video_list.append(image)
    return SnsInfo(post_link=post_link, profile=Profile(f"{username} (@{userid})", user_image_url),
                   content=post_content,
                   images=image_or_video_list)
