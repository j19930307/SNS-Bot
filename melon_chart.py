import json
import os

import requests
from fake_useragent import UserAgent

from song import Song, Artist, Genre


async def top100():
    ua = UserAgent()
    user_agent = ua.random
    headers = {'user-agent': user_agent}
    response = requests.get(headers=headers, url=os.environ["MELON_TOP100_CHART_URL"])
    response = json.loads(response.text)["response"]
    return f"Melon TOP100 {response['RANKDAY']} {response['RANKHOUR']}", get_ranking_list_text(response['SONGLIST'])


async def hot100():
    ua = UserAgent()
    user_agent = ua.random
    headers = {'user-agent': user_agent}
    response = requests.get(headers=headers, url=os.environ["MELON_HOT100_CHART_URL"])
    response = json.loads(response.text)["response"]
    return f"Melon HOT100 {response['RANKDAY']} {response['RANKHOUR']}", get_ranking_list_text(response['SONGLIST'])


async def daily():
    ua = UserAgent()
    user_agent = ua.random
    headers = {'user-agent': user_agent}
    response = requests.get(headers=headers, url=os.environ["MELON_DAILY_CHART_URL"])
    response = json.loads(response.text)["response"]
    return f"Melon 日榜", get_ranking_list_text(response["CHARTLIST"])


async def weekly():
    ua = UserAgent()
    user_agent = ua.random
    headers = {'user-agent': user_agent}
    response = requests.get(headers=headers, url=os.environ["MELON_WEEKLY_CHART_URL"])
    response = json.loads(response.text)["response"]
    return f"Melon 周榜", get_ranking_list_text(response["CHARTLIST"])


async def monthly():
    ua = UserAgent()
    user_agent = ua.random
    headers = {'user-agent': user_agent}
    response = requests.get(headers=headers, url=os.environ["MELON_MONTHLY_CHART_URL"])
    response = json.loads(response.text)["response"]
    return f"Melon 月榜", get_ranking_list_text(response["CHARTLIST"])


def get_song_info(song):
    return Song(
        SONGID=song['SONGID'],
        SONGNAME=song['SONGNAME'],
        ALBUMID=song['ALBUMID'],
        ALBUMNAME=song['ALBUMNAME'],
        ARTISTLIST=[Artist(**artist) for artist in song['ARTISTLIST']],
        PLAYTIME=song['PLAYTIME'],
        GENRELIST=[Genre(**genre) for genre in song['GENRELIST']],
        CURRANK=song['CURRANK'],
        PASTRANK=song['PASTRANK'],
        RANKGAP=song['RANKGAP'],
        RANKTYPE=song['RANKTYPE'],
        ISMV=song['ISMV'],
        ISADULT=song['ISADULT'],
        ISFREE=song['ISFREE'],
        ISHITSONG=song['ISHITSONG'],
        ISHOLDBACK=song['ISHOLDBACK'],
        ISTITLESONG=song['ISTITLESONG'],
        ISSERVICE=song['ISSERVICE'],
        ISTRACKZERO=song['ISTRACKZERO'],
        ALBUMIMG=song['ALBUMIMG'],
        ALBUMIMGPATH=song['ALBUMIMGPATH'],
        ALBUMIMGLARGE=song['ALBUMIMGLARGE'],
        ALBUMIMGSMALL=song['ALBUMIMGSMALL'],
        ISSUEDATE=song['ISSUEDATE'],
        CTYPE=song['CTYPE'],
        CONTSTYPECODE=song['CONTSTYPECODE']
    )


def get_ranking_list_text(song_list: list[dict]):
    ranking_list = []

    for song in song_list:
        info = get_song_info(song)
        curr_rank = info.CURRANK
        rank_gap = info.RANKGAP
        rank_type = info.RANKTYPE

        if rank_type == "UP":
            rank_change = f"(▲{rank_gap})"
        elif rank_type == "DOWN":
            rank_change = f"(▼{rank_gap})"
        elif rank_type == "NONE":
            rank_change = "(-)"
        elif rank_type == "NEW":
            rank_change = "(NEW)"
        else:
            rank_change = ""

        artist_name = ",".join(artist.ARTISTNAME for artist in info.ARTISTLIST)
        # 限制 artist_name 最多30個字
        artist_name = artist_name[:30] + "..." if len(artist_name) > 30 else artist_name
        curr_rank = str(curr_rank).rjust(3)
        rank_change = rank_change.ljust(6)
        ranking_list.append(f"{curr_rank} {rank_change} {artist_name} - {info.SONGNAME}")

    return "```{}```".format('\n'.join(ranking_list))
