"""
fetch_stats.py
Pulls yesterday's final scores + top-performer stats for NBA/NFL/MLB from
ESPN's public scoreboard/summary JSON endpoints. No API key required.
This is read-only public data (scores/box scores), not copyrighted video.
"""

import datetime
import requests

from config import LEAGUES, ESPN_SCOREBOARD_URL, ESPN_SUMMARY_URL


def get_date_str(days_ago=1):
    d = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)
    return d.strftime("%Y%m%d")


def fetch_scoreboard(league_key, date_str):
    league = LEAGUES[league_key]
    url = ESPN_SCOREBOARD_URL.format(
        sport=league["espn_sport"], league=league["espn_league"], date=date_str
    )
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_summary(league_key, event_id):
    league = LEAGUES[league_key]
    url = ESPN_SUMMARY_URL.format(
        sport=league["espn_sport"], league=league["espn_league"], event_id=event_id
    )
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def parse_games(league_key, scoreboard_json):
    """Extract simple, clean game summaries: teams, final score, top performer if available."""
    games = []
    for event in scoreboard_json.get("events", []):
        status = event.get("status", {}).get("type", {}).get("completed", False)
        if not status:
            continue  # skip games not yet final

        competitions = event.get("competitions", [{}])[0]
        competitors = competitions.get("competitors", [])
        if len(competitors) != 2:
            continue

        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        game = {
            "event_id": event.get("id"),
            "name": event.get("shortName", event.get("name", "")),
            "home_team": home.get("team", {}).get("displayName", "Home"),
            "home_score": home.get("score", "0"),
            "away_team": away.get("team", {}).get("displayName", "Away"),
            "away_score": away.get("score", "0"),
            "winner": home.get("team", {}).get("displayName")
            if home.get("winner")
            else away.get("team", {}).get("displayName"),
            "headline": "",
            "top_performers": [],
        }

        # Try to grab a headline / recap note if ESPN provides one
        notes = competitions.get("notes", [])
        if notes:
            game["headline"] = notes[0].get("headline", "")

        games.append(game)
    return games


def enrich_with_leaders(league_key, game):
    """Pull top statistical leaders for a specific game via the summary endpoint."""
    try:
        summary = fetch_summary(league_key, game["event_id"])
    except Exception:
        return game

    leaders = summary.get("leaders", []) or summary.get("boxscore", {}).get("players", [])
    performers = []
    try:
        for team_leader_block in summary.get("leaders", []):
            for category in team_leader_block.get("leaders", []):
                top = category.get("leaders", [{}])[0]
                athlete = top.get("athlete", {}).get("displayName")
                stat = top.get("displayValue")
                if athlete and stat:
                    performers.append(f"{athlete} ({category.get('displayName', 'stat')}: {stat})")
    except Exception:
        pass

    game["top_performers"] = performers[:3]
    return game


def get_daily_recap_data(league_key, days_ago=1):
    date_str = get_date_str(days_ago)
    scoreboard = fetch_scoreboard(league_key, date_str)
    games = parse_games(league_key, scoreboard)
    games = [enrich_with_leaders(league_key, g) for g in games]
    return {
        "league": league_key,
        "date": date_str,
        "games": games,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_daily_recap_data("nba"), indent=2))
