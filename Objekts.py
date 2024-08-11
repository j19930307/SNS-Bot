import json

import requests

seasons = ["Atom01", "Binary01", "Cream01", "Divine01"]
members = [
    "YooYeon", "Mayu", "Xinyu", "NaKyoung", "SoHyun",
    "DaHyun", "Nien", "SeoYeon", "JiYeon", "Kotone",
    "ChaeYeon", "YuBin", "JiWoo", "Kaede", "ShiOn",
    "Lynn", "Sullin", "HyeRin", "ChaeWon", "HaYeon",
    "SooMin", "YeonJi", "JooBin", "SeoAh"
]


class Objekt:
    def __init__(self, front_image: str, back_image: str, copies: int, description: str):
        self.front_image = front_image
        self.back_image = back_image
        self.copies = copies
        self.description = description

    def __str__(self):
        return f"Front Image: {self.front_image}\nBack Image: {self.back_image}\nCopies: {self.copies}\nDescription: {self.description}"


def get_info(season: str, member: str, collection: str):
    metadata_response = requests.get(f"https://apollo.cafe/api/objekts/metadata/{season}-{member}-{collection}")
    by_slug_response = requests.get(f"https://apollo.cafe/api/objekts/by-slug/{season}-{member}-{collection}")

    if metadata_response.status_code != 200 or by_slug_response.status_code != 200:
        return

    metadata = json.loads(metadata_response.text)
    by_slug = json.loads(by_slug_response.text)

    return Objekt(front_image=by_slug["frontImage"], back_image=by_slug["backImage"], copies=metadata["copies"],
                  description=metadata["metadata"]["description"])
