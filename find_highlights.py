# Background music

Drop 3 royalty-free MP3s here, named exactly:

- `nba_theme.mp3`
- `nfl_theme.mp3`
- `mlb_theme.mp3`

I can't auto-download these for you (no general internet access from this
sandbox, and licensing terms vary by track), but sourcing them yourself takes
about 5 minutes and is completely free:

1. **YouTube Audio Library** (studio.youtube.com -> Audio Library) -- built
   for exactly this use case; every track is pre-cleared for YouTube uploads.
   Search "upbeat energetic" for NBA, "epic trailer/cinematic" for NFL,
   "americana/summer" for MLB, or whatever mood you want.
2. **Pixabay Music** (pixabay.com/music) -- free, no attribution required.
3. **Free Music Archive** (freemusicarchive.org) -- filter by CC0/no-attribution.

Download an MP3, rename it to match the filenames above, and commit it to
this folder. If a file is missing, the pipeline just skips the music bed and
uses narration-only audio -- it won't fail the run.
