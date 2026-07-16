# Daily Sports Recap Channel (NBA / NFL / MLB)

Fully automated, fully free daily pipeline that:
1. Pulls yesterday's final scores + top performers (ESPN's public API)
2. Finds the official league highlight video for context (linked, never downloaded)
3. Writes a narration script + blog post
4. Renders an **original** ~90-second video (our own graphics + free TTS + your music)
5. Uploads it to **your** YouTube channel
6. Publishes a matching blog post to a free GitHub Pages site

Everything after initial setup runs unattended, once a day, on GitHub's free
Actions runners. There is no ongoing cost.

**Important:** this does NOT re-upload NBA/NFL/MLB broadcast footage. That's
copyright infringement and gets channels terminated. This pipeline creates
its own graphics/narration video and *links* to the leagues' own official
YouTube uploads instead. Do not attempt to swap in downloaded broadcast clips.

---

## One-time setup (about 30-45 minutes total)

### 1. Create the repo
- Create a new **public** GitHub repo (public repos get unlimited free
  Actions minutes; private repos get 2,000 free min/month, which is still
  plenty for this).
- Push everything in this project folder to it.

### 2. Turn on GitHub Pages for the blog
- Repo Settings -> Pages -> Source: "Deploy from a branch" -> Branch: `main`,
  folder: `/blog`.
- Your blog will be live at `https://<your-username>.github.io/<repo-name>/`
  within a few minutes. This is what you link from your YouTube channel's
  "About" / description / links section.

### 3. Create a Google Cloud project + enable the YouTube Data API
- Go to https://console.cloud.google.com -> create a new project (free).
- APIs & Services -> Library -> enable **YouTube Data API v3**.
- APIs & Services -> Credentials -> **Create Credentials -> API key**.
  Copy it -- this is `YOUTUBE_API_KEY` (used for read-only highlight search).
- Same Credentials page -> **Create Credentials -> OAuth client ID**.
  - Application type: **Desktop app**
  - Copy the **Client ID** and **Client Secret** -- these are
    `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET`.
- OAuth consent screen: set to "External," add your own Google account as a
  test user (you don't need Google's app-review process for personal use).

### 4. Generate a refresh token (one-time, on your own computer)
Run this locally once (not in GitHub Actions) to authorize your own YouTube
channel for uploads:

```bash
pip install google-auth-oauthlib
python - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": "PASTE_YOUR_CLIENT_ID",
            "client_secret": "PASTE_YOUR_CLIENT_SECRET",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)
creds = flow.run_local_server(port=0)
print("REFRESH TOKEN:", creds.refresh_token)
EOF
```

A browser window opens -> log in with the Google account that owns your
YouTube channel -> approve -> the refresh token prints in your terminal.
This token doesn't expire unless you revoke it, so this is a true one-time step.

### 5. Add secrets to GitHub
Repo Settings -> Secrets and variables -> Actions -> New repository secret,
add all four:
- `YOUTUBE_API_KEY`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

### 6. Add background music
See `assets/music/README.md` -- 3 free MP3s, ~5 minutes.

### 7. Test it
Actions tab -> "Daily Sports Recap" workflow -> "Run workflow" (manual
trigger). Check the run logs, check your YouTube channel, check the `blog/`
folder for a new Markdown post.

Recommend setting `PRIVACY_STATUS` to `"unlisted"` in the workflow file for
your first few test runs, then switching to `"public"` once you've reviewed
a couple of outputs.

---

## Ongoing operation

Nothing to do. The workflow runs automatically every day at 13:00 UTC
(9am ET), pulling the prior day's completed games for NBA, NFL, and MLB.

To change the schedule, edit the `cron:` line in
`.github/workflows/daily.yml`. To add/remove a league, edit `LEAGUES` in
`scripts/config.py`.

## Costs (all $0)
- GitHub Actions: free (public repo = unlimited minutes)
- GitHub Pages: free
- ESPN public scoreboard API: free, no key
- YouTube Data API: free tier (10,000 units/day; this uses ~5,400/day for
  3 uploads + searches)
- gTTS narration: free
- YouTube hosting/upload: free

## Known limitations to be upfront about
- gTTS voice quality is functional, not broadcast-polish. If you want a
  noticeably better voice, ElevenLabs and similar have low-cost (not free)
  tiers you could swap in.
- ESPN's scoreboard/summary endpoints are public but unofficial/undocumented;
  they can change shape without notice. If a run fails, check
  `scripts/fetch_stats.py` first.
- YouTube's automated-content and reused-content policies apply to *all*
  channels, including this one. Keep videos genuinely original (your own
  graphics/narration) and you're on solid ground; the risk reappears the
  moment actual broadcast footage gets spliced in.
