from instagrapi import Client

from SnsInfo import SnsInfo, Profile
from discord_bot ***REMOVED***_webhook


def fetch_data_from_instagram(url: str):
    cl = Client()

    # user_id = cl.user_id_from_username(ACCOUNT_USERNAME)
    # medias = cl.user_medias(user_id, 20)

    # https://www.instagram.com/p/CynPhAMJpz0/?igshid=MzRlODBiNWFlZA==

    media_pk = cl.media_pk_from_url(url)
    post_info = cl.media_info(media_pk)

    # 文章內容 caption_text
    # user.username profile_pic_url
    # resources.thumbnail_url video_url
    # like_count

    image_links = [resource.thumbnail_url for resource in post_info.resources]

    return post_info.user.pk, SnsInfo(post_link=url,
                                      profile=Profile(name=f"{post_info.user.full_name} (@{post_info.user.username})",
                                                      url=post_info.user.profile_pic_url),
                                      content=post_info.caption_text, images=image_links)


def get_discord_webhook(id: str):
    if id == "47318740444":  # LIGHTSUM
***REMOVED*** discord_webhook("LIGHTSUM")
    elif id == "42987402481":  # STAYC
***REMOVED*** discord_webhook("STAYC")
    elif id == "61470632061":  # EL7Z UP
***REMOVED*** discord_webhook("EL7Z UP")
