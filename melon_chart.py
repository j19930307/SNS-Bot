import json
import requests
from fake_useragent import UserAgent


async def top100():
    ua = UserAgent()
    user_agent = ua.random
    headers = {'user-agent': user_agent}

    url = "https://m2.melon.com/m6/chart/ent/songChartList.json?cpId=AS40&cpKey=14LNC3&appVer=6.5.8.1"
    response = requests.get(headers=headers, url=url)

    response = json.loads(response.text)["response"]
    rank_list = []

    for song in response["SONGLIST"]:
        curr_rank = song["CURRANK"]
        rank_gap = song["RANKGAP"]
        rank_type = song["RANKTYPE"]

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

        artist_name = ",".join(artist["ARTISTNAME"] for artist in song["ARTISTLIST"])
        song_name = song["SONGNAME"]

        curr_rank = curr_rank.rjust(3)
        rank_change = rank_change.ljust(6)

        rank_list.append(f"{curr_rank} {rank_change} {artist_name} - {song_name}")

    return f"Melon TOP100 {response["RANKDAY"]} {response["RANKHOUR"]}", f"```{'\n'.join(rank_list)}```"
