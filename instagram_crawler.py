from instagrapi import Client

from SnsInfo import SnsInfo, Profile


def fetch_data(cl: Client, url: str):
    media_pk = cl.media_pk_from_url(url)
    post_info = cl.media_info(media_pk)

    user_full_name = post_info.user.full_name
    username = post_info.user.username
    profile_pic_url = post_info.user.profile_pic_url
    caption_text = post_info.caption_text
    profile = Profile(name=f"{user_full_name} (@{username})", url=profile_pic_url)

    media_type = post_info.media_type
    if media_type == 1:  # single photo https://www.instagram.com/p/CwDaXh-vnUY
***REMOVED*** SnsInfo(post_link=url, profile=profile, content=caption_text, images=[post_info.thumbnail_url])
    elif media_type == 2:  # single video https://www.instagram.com/reel/CzA_bJpyL7M
***REMOVED*** SnsInfo(post_link=url, profile=profile, content=caption_text, images=[post_info.thumbnail_url],
                       videos=[post_info.video_url])
    elif media_type == 8:  # album (include photos or videos) https://www.instagram.com/p/Cxnbj7sS1Ns
        images = []
        videos = []
        for resource in post_info.resources:
            if resource.media_type == 1:
                images.append(resource.thumbnail_url)
            elif resource.media_type == 2:
                images.append(resource.thumbnail_url)
                videos.append(resource.video_url)
***REMOVED*** SnsInfo(post_link=url, profile=profile, content=caption_text, images=images, videos=videos)
