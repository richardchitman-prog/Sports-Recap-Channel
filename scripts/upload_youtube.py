"""
upload_youtube.py
Uploads a video to YOUR channel using the YouTube Data API v3 (videos.insert).
Auth uses a long-lived refresh token (see README setup steps) so it can run
unattended inside GitHub Actions -- no browser login during the daily run.

Free tier: 10,000 quota units/day. One upload = 1,600 units, so this supports
up to ~6 uploads/day comfortably (we only need 3, one per league).
"""

import os
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import (
    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN, LEAGUES
)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_authenticated_service():
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(google.auth.transport.requests.Request())
    return build("youtube", "v3", credentials=creds)


def build_description(league_key, recap_data):
    league = LEAGUES[league_key]
    lines = [
        f"Original {league['name']} daily recap -- scores, stats, and standout "
        f"performances, narrated with our own graphics (no broadcast footage used).",
        "",
        "Watch the official full highlights:",
    ]
    seen = set()
    for g in recap_data["games"]:
        h = g.get("official_highlight")
        if h and h["url"] not in seen:
            lines.append(f"- {h['title']}: {h['url']}")
            seen.add(h["url"])
    lines.append("")
    lines.append(f"Official {league['name']} channel: https://youtube.com/{league['official_channel_handle']}")
    lines.append("")
    lines.append("#Shorts #" + league["name"])
    return "\n".join(lines)


def upload_video(league_key, video_path, recap_data, privacy_status="public"):
    league = LEAGUES[league_key]
    date_pretty = recap_data["date"]
    title = f"{league['name']} Daily Recap -- {date_pretty[:4]}-{date_pretty[4:6]}-{date_pretty[6:]} #Shorts"
    description = build_description(league_key, recap_data)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": [league["name"], "sports", "highlights", "recap", "daily"],
            "categoryId": "17",  # Sports
        },
        "status": {
            "privacyStatus": privacy_status,  # "public", "unlisted", or "private"
            "selfDeclaredMadeForKids": False,
        },
    }

    youtube = _get_authenticated_service()
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
    return response  # contains the new video's id, etc.
