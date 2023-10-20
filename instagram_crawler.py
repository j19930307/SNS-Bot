from instagrapi import Client

from SnsInfo import SnsInfo, Profile


def fetch_data_from_instagram(url: str):
    cl = Client()
    cl.login("hungchihung1990", "gaeun940820")

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
***REMOVED*** "https://discord.com/api/webhooks/1162632189553410149/-jjVQRTX3kIhzDbOHecPMi6cOtqixrmS964LOsY082ymcYyDS5lvoyCnuF0FVZu3aZFW"
    elif id == "42987402481":  # STAYC
***REMOVED*** "https://discord.com/api/webhooks/1162736592457310268/9UDH3V-4VhKACIOXvkzEmc-1M-9Sj5o94sOlIewtGWj0WsaEuVFBrpynWNBLNsCnEesk"
    elif id == "61470632061":  # EL7Z UP
***REMOVED*** "https://discord.com/api/webhooks/1152119906981126174/AE_mVQ_WF_DZowhiS8lDSpcZipiy8lM74z7LflPOzbKfE-auqAKiVbimcb-dkxXooOTK"
