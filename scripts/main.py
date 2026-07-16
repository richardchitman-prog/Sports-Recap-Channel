"""
main.py
Daily entry point. Run this once a day (GitHub Actions cron handles the
scheduling -- see .github/workflows/daily.yml).

Pipeline per league (nba, nfl, mlb):
  1. fetch_stats     -> yesterday's final scores + top performers (ESPN public API)
  2. find_highlights -> official league highlight video links (YouTube Data API search)
  3. write_content    -> narration script + blog post text (templated, free)
  4. generate_video   -> original ~90s video: our own graphics + free TTS + music
  5. upload_youtube   -> publish to your channel (YouTube Data API, OAuth)
  6. write blog post  -> Markdown file into docs/_posts (GitHub Pages picks it up)
"""

import os
import sys
import traceback

from config import LEAGUES, OUTPUT_DIR, BLOG_DIR
import fetch_stats
import find_highlights
import write_content
import generate_video
import upload_youtube

# Set to "unlisted" while you're testing so nothing goes public by accident.
PRIVACY_STATUS = os.environ.get("PRIVACY_STATUS", "public")


def run_for_league(league_key):
    print(f"\n=== Processing {league_key.upper()} ===")

    recap_data = fetch_stats.get_daily_recap_data(league_key, days_ago=1)
    if not recap_data["games"]:
        print(f"No completed {league_key.upper()} games for this date -- skipping.")
        return

    recap_data["games"] = find_highlights.find_highlights_for_games(
        league_key, recap_data["games"]
    )

    narration_script = write_content.build_narration_script(league_key, recap_data)
    blog_markdown = write_content.build_blog_post(league_key, recap_data)

    video_path = generate_video.generate_recap_video(
        league_key, recap_data, narration_script, out_dir=OUTPUT_DIR
    )
    print(f"Video rendered: {video_path}")

    try:
        result = upload_youtube.upload_video(
            league_key, video_path, recap_data, privacy_status=PRIVACY_STATUS
        )
        print(f"Uploaded: https://youtube.com/watch?v={result['id']}")
    except Exception:
        print("YouTube upload failed (check credentials/secrets). Video file is still saved locally.")
        traceback.print_exc()

    os.makedirs(BLOG_DIR, exist_ok=True)
    blog_path = os.path.join(BLOG_DIR, f"{recap_data['date']}-{league_key}-recap.md")
    with open(blog_path, "w") as f:
        f.write(blog_markdown)
    print(f"Blog post written: {blog_path}")


def main():
    leagues_to_run = sys.argv[1:] or list(LEAGUES.keys())
    for league_key in leagues_to_run:
        try:
            run_for_league(league_key)
        except Exception:
            print(f"ERROR processing {league_key}:")
            traceback.print_exc()


if __name__ == "__main__":
    main()
