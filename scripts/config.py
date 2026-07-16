"""
Central configuration for the Daily Sports Recap pipeline.
Edit LEAGUES below if a channel handle ever changes.
"""

import os

# ---- Official league YouTube channels (source of truth we link to, never re-upload) ----
LEAGUES = {
    "nba": {
        "name": "NBA",
        "espn_sport": "basketball",
        "espn_league": "nba",
        "official_channel_id": "UCWJ2lWNubArHWmf3FIHbfcQ",  # youtube.com/@NBA
        "official_channel_handle": "@NBA",
        "color": "#C9082A",
    },
    "nfl": {
        "name": "NFL",
        "espn_sport": "football",
        "espn_league": "nfl",
        "official_channel_id": "UCDVYQ4Zhbm3S2dlz7P1GBDg",  # youtube.com/@NFL
        "official_channel_handle": "@NFL",
        "color": "#013369",
    },
   "mlb": {
        "name": "MLB",
        "espn_sport": "baseball",
        "espn_league": "mlb",
        "official_channel_id": "UCoLrcjPV5PbUrUyXq5mjc_A",  # youtube.com/@MLB
        "official_channel_handle": "@MLB",
        "color": "#041E42",
    },
    "epl": {
        "name": "Premier League",
        "espn_sport": "soccer",
        "espn_league": "eng.1",
        "official_channel_id": "UCG5qGWdu8nIRZqJ_GgDwQ-w",  # youtube.com/@premierleague
        "official_channel_handle": "@premierleague",
        "color": "#3D195B",
    },
    "worldcup": {
        "name": "FIFA World Cup",
        "espn_sport": "soccer",
        "espn_league": "fifa.world",
        "official_channel_id": "UCpcTrCXblq78GZrTUTLWeBw",  # youtube.com/@fifa
        "official_channel_handle": "@fifa",
        "color": "#326295",
    },
}

# ESPN's public scoreboard/summary JSON endpoints (no API key required).
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={date}"
ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/summary?event={event_id}"

# YouTube Data API (free tier: 10,000 quota units/day)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")  # for search (read-only, API key is fine)
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

# Video specs
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # vertical, Shorts-friendly; change to 1920x1080 for landscape
VIDEO_FPS = 30
MAX_VIDEO_SECONDS = 90

# Where output files land before upload
OUTPUT_DIR = "output"
BLOG_DIR = "docs/_posts"

# Background music: put your own free-license mp3s here (see assets/music/README.md)
MUSIC_DIR = "assets/music"
DEFAULT_MUSIC = {
    "nba": "assets/music/nba_theme.mp3",
    "nfl": "assets/music/nfl_theme.mp3",
    "mlb": "assets/music/mlb_theme.mp3",
}
