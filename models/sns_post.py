from dataclasses import dataclass
from datetime import datetime


@dataclass
class Author:
    name: str
    url: str


@dataclass(kw_only=True)
class SnsPost:
    post_link: str
    author: Author
    title: str | None = None
    text: str
    images: list[str] | None = None
    videos: list[str] | None = None
    links: list[str] | None = None
    created_at: datetime | None = None
