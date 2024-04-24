import logging
import os
import re
from datetime import datetime

import pyotp
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

logger = logging.getLogger()


class Instagram:
    def __init__(self):
        load_dotenv()
        USERNAME = "foeod_adewd"
        PASSWORD = "juniel19930903"
        self.__client = Client()
        self.__client.load_settings("session.json")
        secret = os.environ["INSTAGRAM_2FA"].replace(" ", "")
        self.__client.login(username=USERNAME,
                            password=PASSWORD, verification_code=pyotp.TOTP(
                secret).now())  # this doesn't actually login using username/password but uses the session
        # check if session is valid
        try:
            self.__client.get_timeline_feed()
        except LoginRequired:
            logger.info("Session is invalid, need to login via username and password")
            old_session = self.__client.get_settings()
            # use the same device uuids across logins
            self.__client.set_settings({})
            self.__client.set_uuids(old_session["uuids"])
            self.__client.login(USERNAME, PASSWORD,
                                verification_code=pyotp.TOTP(os.environ["INSTAGRAM_2FA"].replace(" ",
                                                                                                    "")).now())
            self.__client.dump_settings("session.json")
        # adds a random delay between 1 and 3 seconds after each request
        self.__client.delay_range = [1, 3]

    def get_user_info_from_url(self, url: str):
        pattern = r'instagram\.com/([a-zA-Z0-9_]+)'
        match = re.search(pattern, url)
        if match:
            user_id = match.group(1)
            return self.__client.user_info_by_username_v1(user_id)

    def get_user_id(self, username: str):
        return self.__client.user_id_from_username(username)

    def get_new_posts(self, user_id, updated_at: datetime):
        medias = self.__client.user_medias(user_id, amount=10)
        return [media for media in medias if media.taken_at > updated_at]


# 文章內容 caption_text
# user.username profile_pic_url
# resources.thumbnail_url video_url
# like_count

# url = "https://www.instagram.com/p/C5vWTepSN9G"

# image_links = [resource.thumbnail_url for resource in post_info.resources]
#
# media_pk = cl.media_pk_from_url(url)
# post_info = cl.media_info(media_pk)
# print(post_info.caption_text)


# cl.delay_range = [1, 3]
#

Instagram()
