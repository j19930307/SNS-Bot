from discord import Embed

from models.sns_post import SnsPost

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

DOMAIN_TWITTER = "twitter.com"
DOMAIN_X = "x.com"
DOMAIN_INSTAGRAM = "instagram.com"
DOMAIN_WEVERSE = "weverse.io"
DOMAIN_THREADS = "threads.com"
DOMAIN_BERRIZ = "berriz.in"

DOMAIN_H1KEY = "h1key-official.com"
DOMAIN_H1KEY_BSTAGE = "h1key.bstage.in"
DOMAIN_YEEUN_BSTAGE = "yeeun.bstage.in"
DOMAIN_PURPLE_KISS = "purplekiss.co.kr"
DOMAIN_KISS_OF_LIFE = "kissoflife-official.com"
DOMAIN_KISS_OF_LIFE_BSTAGE = "kissoflife.bstage.in"

DOMAINS_BSTAGE = {
    DOMAIN_H1KEY,
    DOMAIN_H1KEY_BSTAGE,
    DOMAIN_YEEUN_BSTAGE,
    DOMAIN_PURPLE_KISS,
    DOMAIN_KISS_OF_LIFE,
    DOMAIN_KISS_OF_LIFE_BSTAGE,
}

# ---------------------------------------------------------------------------
# Source icon mapping  (domain -> (label, icon_url))
# ---------------------------------------------------------------------------

_SOURCE_MAP: dict[str, tuple[str, str]] = {
    DOMAIN_TWITTER:   ("X",         "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/X_icon_2.svg/2048px-X_icon_2.svg.png"),
    DOMAIN_X:         ("X",         "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/X_icon_2.svg/2048px-X_icon_2.svg.png"),
    DOMAIN_INSTAGRAM: ("Instagram", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Instagram_icon.png/600px-Instagram_icon.png"),
    DOMAIN_WEVERSE:   ("Weverse",   "https://image.winudf.com/v2/image1/Y28uYmVueC53ZXZlcnNlX2ljb25fMTY5NjQwNDE0MF8wMTM/icon.webp?w=140&fakeurl=1&type=.webp"),
    DOMAIN_THREADS:   ("Threads",   "https://cdn.iconscout.com/icon/free/png-256/free-threads-logo-icon-svg-download-png-8461527.png"),
    DOMAIN_BERRIZ:    ("Berriz",    "https://play-lh.googleusercontent.com/vr-o5CiOCByufCykA7PWFFQSppaEpSQAjXvm5ehthw2IiHQ8L0umnOQdqUmZAEUjkgeJ"),
}

_BSTAGE_SOURCE: tuple[str, str] = ("b.stage", "https://i.imgur.com/xekJ8pd.png")


def resolve_source(domain: str) -> tuple[str, str] | None:
    """Return (label, icon_url) for a given domain, or None if unknown."""
    if domain in DOMAINS_BSTAGE:
        return _BSTAGE_SOURCE
    return _SOURCE_MAP.get(domain)


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------

def _base_embed(
    *,
    sns_post: SnsPost,
    description: str,
    source: tuple[str, str] | None,
) -> Embed:
    embed = Embed(
        title=sns_post.title,
        description=description,
        url=sns_post.post_link,
        timestamp=sns_post.created_at,
    ).set_author(
        name=sns_post.author.name,
        icon_url=sns_post.author.url,
    )

    if source:
        embed.set_footer(text=source[0], icon_url=source[1])

    return embed


def _resolve_source_from_post(sns_post: SnsPost) -> tuple[str, str] | None:
    from utils.url_utils import extract_domain
    return resolve_source(extract_domain(sns_post.post_link) or "")


def build_embeds(sns_post: SnsPost) -> list[Embed]:
    """Build embeds with up to 4 images attached (normal preview)."""
    source = _resolve_source_from_post(sns_post)
    description = (sns_post.text or "")[:4096]
    images = sns_post.images

    def base() -> Embed:
        return _base_embed(sns_post=sns_post, description=description, source=source)

    if not images:
        return [base()]

    # Discord groups embeds with the same URL into one block (max 4 images)
    embeds = [base().set_image(url=images[0])]
    for image_url in images[1:4]:
        embeds.append(Embed(url=sns_post.post_link).set_image(url=image_url))

    return embeds


def build_text_embed(sns_post: SnsPost) -> list[Embed]:
    """Build a single embed without images (used when media is uploaded as files)."""
    source = _resolve_source_from_post(sns_post)
    description = (sns_post.text or "")[:4096]
    return [_base_embed(sns_post=sns_post, description=description, source=source)]


# ---------------------------------------------------------------------------
# Mention helper
# ---------------------------------------------------------------------------

def is_bot_mentioned(message, bot_id: int) -> bool:
    """Return True if the bot is mentioned directly or via a role."""
    if bot_id in message.raw_mentions:
        return True
    return any(
        member.id == bot_id
        for role in message.role_mentions
        for member in role.members
    )