from datetime import datetime


class Profile:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class SnsInfo:
    def __init__(self, post_link: str, profile: Profile, content: str, images: list, videos: list = None,
                 attachments: list = None, title: str = None, timestamp: datetime = None):
        self.post_link = post_link
        self.profile = profile
        self.title = title
        self.content = content
        self.images = images
        self.videos = videos
        self.attachments = attachments
        self.timestamp = timestamp

    def __str__(self):
        return f"link: {self.post_link}\nprofile: {self.profile.name} {self.profile.url}\ncontent: {self.content}\nimages: {self.images}\nvideos: {self.videos}\nattachments: {self.attachments}\ntimestamp: {self.timestamp}"
