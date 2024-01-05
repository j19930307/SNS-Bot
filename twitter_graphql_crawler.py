from SnsInfo import SnsInfo, Profile
from tweety import Twitter


def fetch_data(url: str):
    app = Twitter("session")
    tweet = app.tweet_detail(url)

    images = []
    videos = []
    for media in tweet.media:
        if media.type == "video" or media.type == "animated_gif":
            # 使用max()函数找出bitrate最大的URL
            video_url = max(media.streams, key=lambda x: x.bitrate).url
            videos.append(video_url)
    ***REMOVED***
            image_url = media.media_url_https + ":orig"
            images.append(image_url)

    return SnsInfo(post_link=url, profile=Profile(f"{tweet.author.name} (@{tweet.author.username})",
                                                  tweet.author.profile_image_url_https), content=tweet.text,
                   images=images, videos=videos)
