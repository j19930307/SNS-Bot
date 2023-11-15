class Profile:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class SnsInfo:
    def __init__(self, post_link: str, profile: Profile, content: str, images: list, videos: list = None,
                 title: str = None):
        self.post_link = post_link
        self.profile = profile
        self.title = title
        self.content = content
        self.images = images
        self.videos = videos
