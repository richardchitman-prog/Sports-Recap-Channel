"""
comment_bot.py
Scans comments on your channel's recent videos and:
  1. Flags likely spam (promo links, "check my channel", crypto/followers
     spam, etc.) by setting moderationStatus to "heldForReview" -- NOT
     auto-deleted, so false positives just sit in your moderation queue
     for a manual look instead of vanishing.
  2. Auto-replies to comments matching known FAQ patterns (about the
     music, whether footage is real, upload schedule, etc.) -- once per
     comment, tracked via a small local state file so it never double-replies.

Requires the OAuth refresh token to include the broader
"https://www.googleapis.com/auth/youtube.force-ssl" scope (uploading alone
only needs "youtube.upload"). See README for how to regenerate it.
"""

import os
import re
import json

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import (
    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

STATE_PATH = os.path.join(os.path.dirname(__file__), "state", "processed_comments.json")
MAX_STATE_SIZE = 5000  # cap so the state file doesn't grow forever

# ---------------------------------------------------------------------------
# Spam heuristics -- deliberately conservative. Anything that matches gets
# held for review, not deleted, so a false positive costs you a click in
# YouTube Studio rather than losing a real comment.
# ---------------------------------------------------------------------------
SPAM_PATTERNS = [
    r"\bcheck (out )?my channel\b",
    r"\bsubscribe to my\b",
    r"\bfollow me (on|at)\b",
    r"\bfree (followers|subscribers|views)\b",
    r"\bmake \$?\d+.{0,15}(day|week|hour)\b",
    r"\bforex\b",
    r"\bcrypto\b.*\b(profit|investment|trading)\b",
    r"(https?://|www\.)\S+",  # any raw link
    r"\bDM me\b",
    r"\bwhatsapp\b",
    r"\btelegram\b.*\b(contact|dm|message)\b",
]
SPAM_RE = re.compile("|".join(SPAM_PATTERNS), re.IGNORECASE)


def is_probably_spam(text):
    if SPAM_RE.search(text):
        return True
    # excessive caps: >70% uppercase letters in a longish comment
    letters = [c for c in text if c.isalpha()]
    if len(letters) > 20:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.7:
            return True
    return False


# ---------------------------------------------------------------------------
# FAQ auto-replies -- (pattern, reply text). First match wins per comment.
# ---------------------------------------------------------------------------
FAQ_REPLIES = [
    (
        re.compile(r"\b(what|which)\b.{0,15}\b(song|music|track)\b", re.IGNORECASE),
        "Great question! The background music is royalty-free, sourced from the "
        "YouTube Audio Library / Pixabay Music. Full game highlights are always "
        "linked in the description if you want the official broadcast footage!",
    ),
    (
        re.compile(r"\b(is this|real footage|actual (game|game footage|broadcast))\b", re.IGNORECASE),
        "This video uses original graphics and narration built from public stats, "
        "not broadcast footage -- that's why it looks different from a highlight "
        "reel. Check the description for a link to the league's official highlights!",
    ),
    (
        re.compile(r"\bwhen('s| is)?\b.{0,15}\b(next|new)\b.{0,10}\bvideo\b", re.IGNORECASE),
        "New recaps post daily! Subscribe and turn on notifications so you don't miss one.",
    ),
    (
        re.compile(r"\bwhere\b.{0,15}\b(get|source|data|stats)\b", re.IGNORECASE),
        "The scores and stats come from public league data feeds, pulled fresh every day.",
    ),
]


def _load_state():
    if not os.path.exists(STATE_PATH):
        return set()
    try:
        with open(STATE_PATH, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_state(processed_ids):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    # keep only the most recent MAX_STATE_SIZE ids to prevent unbounded growth
    trimmed = list(processed_ids)[-MAX_STATE_SIZE:]
    with open(STATE_PATH, "w") as f:
        json.dump(trimmed, f)


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


def get_recent_video_ids(youtube, channel_id=None, max_videos=10):
    """
    Get the most recent uploads on YOUR channel (the authenticated user's
    channel, via mine=True) so we know which videos to scan for new comments.
    """
    channels_resp = youtube.channels().list(part="contentDetails", mine=True).execute()
    items = channels_resp.get("items", [])
    if not items:
        return []
    uploads_playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    playlist_resp = youtube.playlistItems().list(
        part="contentDetails", playlistId=uploads_playlist, maxResults=max_videos
    ).execute()
    return [item["contentDetails"]["videoId"] for item in playlist_resp.get("items", [])]


def process_video_comments(youtube, video_id, processed_ids):
    held_count = 0
    replied_count = 0

    try:
        resp = youtube.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=100, order="time", textFormat="plainText"
        ).execute()
    except Exception as e:
        print(f"Could not fetch comments for {video_id} (comments may be disabled): {e}")
        return held_count, replied_count

    for item in resp.get("items", []):
        top_comment = item["snippet"]["topLevelComment"]
        comment_id = top_comment["id"]
        if comment_id in processed_ids:
            continue

        text = top_comment["snippet"].get("textDisplay", "")

        if is_probably_spam(text):
            try:
                youtube.comments().setModerationStatus(
                    id=comment_id, moderationStatus="heldForReview"
                ).execute()
                held_count += 1
                print(f"Held for review (possible spam): {text[:60]!r}")
            except Exception as e:
                print(f"Could not moderate comment {comment_id}: {e}")
            processed_ids.add(comment_id)
            continue

        for pattern, reply_text in FAQ_REPLIES:
            if pattern.search(text):
                try:
                    youtube.comments().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "parentId": comment_id,
                                "textOriginal": reply_text,
                            }
                        },
                    ).execute()
                    replied_count += 1
                    print(f"Replied to: {text[:60]!r}")
                except Exception as e:
                    print(f"Could not reply to comment {comment_id}: {e}")
                break

        processed_ids.add(comment_id)

    return held_count, replied_count


def run(max_videos=10):
    youtube = _get_authenticated_service()
    processed_ids = _load_state()

    video_ids = get_recent_video_ids(youtube, max_videos=max_videos)
    if not video_ids:
        print("No recent videos found on this channel.")
        return

    total_held, total_replied = 0, 0
    for video_id in video_ids:
        held, replied = process_video_comments(youtube, video_id, processed_ids)
        total_held += held
        total_replied += replied

    _save_state(processed_ids)
    print(f"\nDone. Held for review: {total_held}. Auto-replied: {total_replied}.")


if __name__ == "__main__":
    run()
