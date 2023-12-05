from discord import Embed, message

from SnsInfo import SnsInfo

DOMAIN_TWITTER = "twitter.com"
DOMAIN_X = "x.com"
DOMAIN_INSTAGRAM = "instagram.com"
DOMAIN_WEVERSE = "weverse.io"
DOMAIN_H1KEY = "h1key-official.com"
DOMAIN_YEEUN = "yeeun.bstage.in"
DOMAIN_PURPLE_KISS = "purplekiss.co.kr"
DOMAIN_BSTAGE = [DOMAIN_H1KEY, DOMAIN_YEEUN, DOMAIN_PURPLE_KISS]


def post_source(url: str):
    if DOMAIN_TWITTER in url or DOMAIN_X in url:
***REMOVED*** "X", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/X_icon_2.svg/2048px-X_icon_2.svg.png"
    elif DOMAIN_INSTAGRAM in url:
***REMOVED*** "Instagram", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Instagram_icon.png/600px-Instagram_icon.png"
    elif DOMAIN_WEVERSE in url:
***REMOVED*** "Weverse", "https://image.winudf.com/v2/image1/Y28uYmVueC53ZXZlcnNlX2ljb25fMTY5NjQwNDE0MF8wMTM/icon.webp?w=140&fakeurl=1&type=.webp"


def generate_embeds(username: str, sns_info: SnsInfo):
    embeds = []
    # 圖片訊息，Embed 的 url 如果一樣，最多可以 4 張以下的合併在一個區塊
    for index, image_url in enumerate(sns_info.images[slice(4)]):
        if index == 0:
            source = post_source(sns_info.post_link)
            embed = (
                Embed(title=sns_info.title, description=sns_info.content, url=sns_info.post_link).set_author(
                    name=sns_info.profile.name, icon_url=sns_info.profile.url)
                .set_image(url=image_url)
                .insert_field_at(index=0, name="使用者", value=username))
            if source is not None:
                embed.set_footer(text=post_source(sns_info.post_link)[0],
                                 icon_url=post_source(sns_info.post_link)[1])
            embeds.append(embed)
    ***REMOVED***
            embeds.append(Embed(url=sns_info.post_link)
                          .set_author(name=sns_info.profile.name, url=sns_info.profile.url)
                          .set_image(url=image_url))
***REMOVED***
        embeds.append(Embed(title=sns_info.title, description=sns_info.content, url=sns_info.post_link).set_author(
                    name=sns_info.profile.name, icon_url=sns_info.profile.url)
                .insert_field_at(index=0, name="使用者", value=username))

    return embeds


def mentions(message: message, bot_id: int):
    if bot_id in message.raw_mentions:
***REMOVED*** True
***REMOVED***
        for role in message.role_mentions:
            for member in role.members:
                if member.id == bot_id:
            ***REMOVED*** True
    return False
