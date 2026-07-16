"""
find_highlights.py
Uses the YouTube Data API (read-only `search.list`) to find each league's
OFFICIAL highlight video for a given game/day, restricted to that league's
official channel_id. We only ever store the video's URL/title/thumbnail --
never its actual video file. This is what gets embedded/linked in the blog
post and video description.

Requires: YOUTUBE_API_KEY (a free Google Cloud API key with YouTube Data API v3
enabled). Search costs 100 quota units/call; free daily quota is 10,000 units,
so this comfortably supports 3 leagues/day.
"""

import requests
from config import LEAGUES, YOUTUBE_API_KEY

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def find_official_highlight(league_key, query_hint):
    """
    query_hint: e.g. 'Lakers vs Celtics highlights' or 'NFL Week 5 highlights'
    Returns dict with title/url/thumbnail, or None if not found / no API key set.
    """
    if not YOUTUBE_API_KEY:
        return None

    league = LEAGUES[league_key]
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "channelId": league["official_channel_id"],
        "q": query_hint,
        "type": "video",
        "order": "date",
        "maxResults": 1,
    }
    try:
        resp = requests.get(SEARCH_URL, params=params, timeout=20)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception:
        return None

    if not items:
        return None

    item = items[0]
    video_id = item.get("id", {}).get("videoId")
    if not video_id:
        return None

    snippet = item.get("snippet", {})
    return {
        "title": snippet.get("title", ""),
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
    }


def find_highlights_for_games(league_key, games):
    for g in games:
        query_hint = g.get("name") or f"{g['away_team']} vs {g['home_team']} highlights"
        g["official_highlight"] = find_official_highlight(league_key, f"{query_hint} highlights")
    return games


if __name__ == "__main__":
    print("This module is invoked from main.py -- see README for setup.")
