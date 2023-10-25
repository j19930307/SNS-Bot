import json

with open("tweet_sample.txt", encoding="utf-8") as json_file:
    root = json.loads(json_file.read())
    print(root["data"]["tweetResult"]["result"]["core"]["user_results"]["result"]["legacy"]["name"])
    print(root["data"]["tweetResult"]["result"]["core"]["user_results"]["result"]["legacy"]["screen_name"])
    print(root["data"]["tweetResult"]["result"]["core"]["user_results"]["result"]["legacy"]["profile_image_url_https"])
    print(root["data"]["tweetResult"]["result"]["legacy"]["full_text"])
    media_list = root["data"]["tweetResult"]["result"]["legacy"]["extended_entities"]["media"]

    image_or_video_list = []

    for media in media_list:
        if media["type"] == "video":
            # 使用max()函数找出bitrate最大的URL
            video_url = max(media["video_info"]["variants"], key=lambda x: x.get('bitrate', 0))["url"]
            image_or_video_list.append(video_url)
        elif media["type"] == "photo":
            image = media["media_url_https"]
            image_or_video_list.append(image)

    print(image_or_video_list)