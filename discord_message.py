class Image:
    def __init__(self, url):
        self.url = url


class Author:
    def __init__(self, name, icon_url):
        self.name = name
        self.icon_url = icon_url


class Embed:
    def __init__(self, author: Author = None, description: str = None, image: Image = None, url: str = None):
        self.author = author
        self.description = description
        self.image = image
        self.url = url


class Message:
    def __init__(self, content, embeds: list[Embed]):
        self.content = content
        self.embeds = embeds
