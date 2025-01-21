import os
import re
from datetime import datetime

import requests
from dotenv import load_dotenv
from lxml import html
import json
import googleapiclient.discovery


def get_channel_name(channel_handle: str):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=os.environ["YOUTUBE_DATA_API_KEY"])
    request = youtube.channels().list(
        part="snippet",
        forHandle=channel_handle
    )
    response = request.execute()

    if response.get('items', None):
        channel_name = response['items'][0]['snippet']['title']
        return channel_name
    else:
        return None


def get_latest_videos(channel_handle: str):
    videos_id = []
    text = requests.get(f'https://www.youtube.com/@{channel_handle}/videos').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

    for i in range(len(tabs)):
        tabRemenderer = tabs[i].get('tabRenderer')
        if tabRemenderer is None: break
        # 從 tab 的 url 判斷哪一個是影片 (videos)
        url = tabRemenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
        if url.rsplit("/", 1)[-1] == "videos":
            contents = tabs[i]['tabRenderer']['content']['richGridRenderer']['contents']

            for content in contents:
                richItemRenderer = content.get('richItemRenderer')
                if richItemRenderer is None: break
                videoRenderer = richItemRenderer['content']['videoRenderer']
                video_id = videoRenderer['videoId']
                videos_id.append(video_id)

    return videos_id


def get_latest_shorts(channel_handle: str):
    videos_id = []
    text = requests.get(f'https://www.youtube.com/@{channel_handle}/shorts').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

    for i in range(len(tabs)):
        tabRemenderer = tabs[i].get('tabRenderer')
        if tabRemenderer is None: break
        # 從 tab 的 url 判斷哪一個是短影片 (shorts)
        url = tabRemenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
        if url.rsplit("/", 1)[-1] == "shorts":
            contents = tabs[i]['tabRenderer']['content']['richGridRenderer']['contents']
            for content in contents:
                richItemRenderer = content.get('richItemRenderer')
                if richItemRenderer is not None:
                    reelItemRenderer = richItemRenderer['content'].get('reelItemRenderer')
                    shortsLockupViewModel = richItemRenderer['content'].get('shortsLockupViewModel')
                    if reelItemRenderer is not None:
                        video_id = reelItemRenderer['videoId']
                        videos_id.append(video_id)
                    elif shortsLockupViewModel is not None:
                        video_id = shortsLockupViewModel['onTap']['innertubeCommand']['reelWatchEndpoint']['videoId']
                        videos_id.append(video_id)

    return videos_id


def get_latest_streams(channel_handle: str):
    videos_id = []
    text = requests.get(f'https://www.youtube.com/@{channel_handle}/streams').text
    tree = html.fromstring(text)
    ytVariableName = 'ytInitialData'
    ytVariableDeclaration = ytVariableName + ' = '
    for script in tree.xpath('//script'):
        scriptContent = script.text_content()
        if ytVariableDeclaration in scriptContent:
            ytVariableData = json.loads(scriptContent.split(ytVariableDeclaration)[1][:-1])
            break

    tabs = ytVariableData['contents']['twoColumnBrowseResultsRenderer']['tabs']

    for i in range(len(tabs)):
        tabRemenderer = tabs[i].get('tabRenderer')
        if tabRemenderer is None: break
        # 從 tab 的 url 判斷哪一個是直播 (streams)
        url = tabRemenderer['endpoint']['commandMetadata']['webCommandMetadata']['url']
        if url.rsplit("/", 1)[-1] == "streams":
            contents = tabs[i]['tabRenderer']['content']['richGridRenderer']['contents']
            for content in contents:
                richItemRenderer = content.get('richItemRenderer', None)
                if richItemRenderer is not None:
                    videoRenderer = richItemRenderer['content']['videoRenderer']
                    video_id = videoRenderer['videoId']
                    videos_id.append(video_id)
    return videos_id


def get_video_published_at(video_id: str):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=os.environ["YOUTUBE_DATA_API_KEY"])
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()

    if response['items']:
        published_at = response['items'][0]['snippet']['publishedAt']
        # 轉換成 datetime 對象
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    else:
        return None