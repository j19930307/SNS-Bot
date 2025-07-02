import re
from datetime import datetime, timezone

import requests

from sns_info import SnsInfo, Profile

pattern = re.compile(r'/([^/]+)/board/([^/]+)/post/([^/]+)/')


def fetch_data(url: str):
    match = pattern.search(url)
    if not match:
        return None

    group_name, board_id, post_id = match.groups()
    community_id = get_community_id(group_name)
    if community_id:
        return get_post_info(board_id=board_id, community_id=community_id, group_name=group_name, post_id=post_id)
    return None


def get_community_id(group_name: str):
    url = f"https://svc-api.berriz.in/service/v1/community/id/{group_name}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get('data', {}).get('communityId')
    except Exception as e:
        print(f"Error getting community_id for {group_name}: {e}")
        return None


def get_board_id(community_id: str):
    url = f"https://svc-api.berriz.in/service/v1/community/info/{community_id}/menus"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            menus = response.json().get("data", {}).get("menus", [])
            for menu in menus:
                if menu['type'] == 'board' and menu['iconType'] == 'artist':
                    return menu['id']
    except Exception as e:
        print(f"Error getting board_id for {community_id}: {e}")
        return None


def get_post_info(board_id: str, community_id: str, group_name: str, post_id: str):
    url = f"https://svc-api.berriz.in/service/v1/community/{community_id}/post/{post_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None

        data = response.json().get('data', {})
        post = data.get('post', {})
        writer = data.get('writer', {})

        body = post.get('body', '')
        created_at = post.get('createdAt', '')
        image_urls = [item.get("imageUrl") for item in post.get('media', {}).get('photo', []) if item.get("imageUrl")]
        writer_name = writer.get('name', 'Unknown')
        writer_image = writer.get('imageUrl', '')

        try:
            dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)

        return SnsInfo(
            post_link=f"https://berriz.in/en/{group_name}/board/{board_id}/post/{post_id}/",
            profile=Profile(name=writer_name, url=writer_image),
            content=body,
            images=image_urls,
            timestamp=dt
        )
    except Exception as e:
        print(f"Error fetching post info: {e}")
        return None
