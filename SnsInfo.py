class Profile:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class SnsInfo:
    def __init__(self, post_link: str, profile: Profile, content: str, images: list):
        self.post_link = post_link
        self.profile = profile
        self.content = content
        self.images = images
