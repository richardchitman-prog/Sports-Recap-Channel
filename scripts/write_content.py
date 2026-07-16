"""
write_content.py
Turns raw stats/highlight data into:
  1. A ~90-second narration script (for the video voiceover)
  2. A blog post (Markdown) with real analysis/context

This is fully templated/rule-based -- free, deterministic, no LLM API key
needed. If you have an ANTHROPIC_API_KEY and want richer prose, see the
optional `polish_with_claude()` function at the bottom (off by default).
"""

import datetime

WORDS_PER_SECOND = 2.5  # rough average speaking pace -> keeps narration near 90s


def build_narration_script(league_key, recap_data, max_games=4):
    league_name = league_key.upper()
    date_str = recap_data["date"]
    games = recap_data["games"][:max_games]

    lines = [f"Here's your {league_name} recap for {_pretty_date(date_str)}."]

    for g in games:
        score_line = (
            f"{g['away_team']} {g['away_score']}, {g['home_team']} {g['home_score']}. "
            f"{g['winner']} takes it."
        )
        lines.append(score_line)
        if g["top_performers"]:
            lines.append(f"Top performer: {g['top_performers'][0]}.")

    lines.append(f"That's your {league_name} rundown -- full highlights linked below.")

    script = " ".join(lines)

    # Trim to fit ~90 seconds of narration
    max_words = int(WORDS_PER_SECOND * 90)
    words = script.split()
    if len(words) > max_words:
        script = " ".join(words[:max_words])

    return script


def build_blog_post(league_key, recap_data):
    league_name = league_key.upper()
    date_str = recap_data["date"]
    pretty = _pretty_date(date_str)
    games = recap_data["games"]

    fm = (
        "---\n"
        f"title: \"{league_name} Recap - {pretty}\"\n"
        f"date: {_iso_date(date_str)}\n"
        f"categories: [{league_key}]\n"
        "layout: post\n"
        "---\n\n"
    )

    body = [f"## {league_name} Scores & Standouts -- {pretty}\n"]

    if not games:
        body.append("No completed games found for this date.\n")
    for g in games:
        body.append(f"### {g['away_team']} @ {g['home_team']}")
        body.append(f"**Final:** {g['away_team']} {g['away_score']} -- {g['home_team']} {g['home_score']}")
        body.append(f"**Winner:** {g['winner']}\n")
        if g.get("headline"):
            body.append(f"{g['headline']}\n")
        if g["top_performers"]:
            body.append("**Top performers:**")
            for p in g["top_performers"]:
                body.append(f"- {p}")
            body.append("")
        highlight = g.get("official_highlight")
        if highlight:
            body.append(
                f"[Watch official {league_name} highlights \u2192]({highlight['url']})\n"
            )
        body.append("---\n")

    return fm + "\n".join(body)


def _pretty_date(yyyymmdd):
    d = datetime.datetime.strptime(yyyymmdd, "%Y%m%d")
    return d.strftime("%B %d, %Y")


def _iso_date(yyyymmdd):
    d = datetime.datetime.strptime(yyyymmdd, "%Y%m%d")
    return d.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# OPTIONAL: if you want noticeably better narration/blog prose and are fine
# paying normal Anthropic API rates (this step is NOT free), you can swap in
# a call to Claude here. Left disabled by default per your "free" requirement.
# ---------------------------------------------------------------------------
def polish_with_claude(script_text):
    raise NotImplementedError("Disabled by default -- costs API credits.")
