from discord import Embed, message

from sns_info import SnsInfo
from utils.url_utils import shorten_url

DOMAIN_TWITTER = "twitter.com"
DOMAIN_X = "x.com"
DOMAIN_INSTAGRAM = "instagram.com"
DOMAIN_WEVERSE = "weverse.io"
DOMAIN_H1KEY_1 = "h1key-official.com"
DOMAIN_H1KEY_2 = "h1key.bstage.in"
DOMAIN_YEEUN = "yeeun.bstage.in"
DOMAIN_PURPLE_KISS = "purplekiss.co.kr"
DOMAIN_KISS_OF_LIFE_1 = "kissoflife-official.com"
DOMAIN_KISS_OF_LIFE_2 = "kissoflife.bstage.in"
DOMAIN_BSTAGE = [DOMAIN_H1KEY_1, DOMAIN_H1KEY_2, DOMAIN_YEEUN, DOMAIN_PURPLE_KISS, DOMAIN_KISS_OF_LIFE_1,
                 DOMAIN_KISS_OF_LIFE_2]
DOMAIN_THREADS = "threads.com"
DOMAIN_BERRIZ = "berriz.in"


def post_source(url: str):
    if DOMAIN_TWITTER in url or DOMAIN_X in url:
        return "X", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/X_icon_2.svg/2048px-X_icon_2.svg.png"
    elif DOMAIN_INSTAGRAM in url:
        return "Instagram", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Instagram_icon.png/600px-Instagram_icon.png"
    elif DOMAIN_WEVERSE in url:
        return "Weverse", "https://image.winudf.com/v2/image1/Y28uYmVueC53ZXZlcnNlX2ljb25fMTY5NjQwNDE0MF8wMTM/icon.webp?w=140&fakeurl=1&type=.webp"
    elif any(ext in DOMAIN_BSTAGE for ext in url):
        return "b.stage", "https://i.imgur.com/xekJ8pd.png"


def generate_embeds(username: str, sns_info: SnsInfo):
    embeds = []
    source = post_source(sns_info.post_link)
    description = sns_info.content[:2048]

    # 將過長的圖片連結替換成短網址
    sns_info.images = [
        shorten_url(image) if len(image) > 100 else image
        for image in sns_info.images
    ]

    # 圖片訊息，Embed 的 url 如果一樣，最多可以 4 張以下的合併在一個區塊
    for index, image_url in enumerate(sns_info.images[slice(4)]):
        if index == 0:
            embed = (
                Embed(title=sns_info.title, description=description, url=sns_info.post_link,
                      timestamp=sns_info.timestamp).set_author(
                    name=sns_info.profile.name, icon_url=sns_info.profile.url)
                .set_image(url=image_url))
            if username is not None and username != "":
                embed.insert_field_at(index=0, name="使用者", value=username)
            if source is not None:
                embed.set_footer(text=post_source(sns_info.post_link)[0], icon_url=post_source(sns_info.post_link)[1])
            embeds.append(embed)
        else:
            embeds.append(Embed(url=sns_info.post_link)
                          .set_author(name=sns_info.profile.name, url=sns_info.profile.url)
                          .set_image(url=image_url))
    else:
        embed = Embed(title=sns_info.title, description=description, url=sns_info.post_link,
                      timestamp=sns_info.timestamp).set_author(
            name=sns_info.profile.name, icon_url=sns_info.profile.url)
        if username is not None and username != "":
            embed.insert_field_at(index=0, name="使用者", value=username)
        if source is not None:
            embed.set_footer(text=post_source(sns_info.post_link)[0], icon_url=post_source(sns_info.post_link)[1])
        embeds.append(embed)

    return embeds


def mentions(message: message, bot_id: int):
    if bot_id in message.raw_mentions:
        return True
    else:
        for role in message.role_mentions:
            for member in role.members:
                if member.id == bot_id:
                    return True
    return False
