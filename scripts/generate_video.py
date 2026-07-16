"""
generate_video.py
Builds an ORIGINAL video (no broadcast footage) for one league's daily recap:
  - Text/graphics slides per game (Pillow)
  - Free text-to-speech narration (gTTS -- Google Translate TTS, no key needed)
  - Optional background music bed (royalty-free file you supply, see assets/music/README.md)
Output: an mp4 under MAX_VIDEO_SECONDS, safe to upload as fully original content.
"""

import os
import datetime
from gtts import gTTS
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, afx
)
from PIL import Image, ImageDraw, ImageFont

from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, MAX_VIDEO_SECONDS, LEAGUES, DEFAULT_MUSIC


def _load_font(size):
    candidates = [
        "assets/fonts/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _make_slide(text_lines, bg_color, out_path):
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    title_font = _load_font(70)
    body_font = _load_font(46)

    y = VIDEO_HEIGHT // 2 - (len(text_lines) * 60) // 2
    for i, line in enumerate(text_lines):
        font = title_font if i == 0 else body_font
        w = draw.textlength(line, font=font)
        x = (VIDEO_WIDTH - w) / 2
        draw.text((x, y), line, font=font, fill="white")
        y += 90 if i == 0 else 60

    img.save(out_path)
    return out_path


def _tts_audio(text, out_path):
    tts = gTTS(text=text, lang="en")
    tts.save(out_path)
    return out_path


def _pretty(yyyymmdd):
    d = datetime.datetime.strptime(yyyymmdd, "%Y%m%d")
    return d.strftime("%B %d, %Y")


def generate_recap_video(league_key, recap_data, narration_script, out_dir="output"):
    os.makedirs(out_dir, exist_ok=True)
    league = LEAGUES[league_key]
    date_str = recap_data["date"]

    # 1) Narration audio
    narration_path = os.path.join(out_dir, f"{league_key}_{date_str}_narration.mp3")
    _tts_audio(narration_script, narration_path)
    narration_clip = AudioFileClip(narration_path)
    total_duration = min(narration_clip.duration, MAX_VIDEO_SECONDS)

    # 2) Build slides: intro + one per game (max 4) sized to fill total_duration
    games = recap_data["games"][:4]
    slide_texts = [[f"{league['name']} RECAP", _pretty(date_str)]]
    for g in games:
        slide_texts.append([
            f"{g['away_team']} {g['away_score']} - {g['home_team']} {g['home_score']}",
            (g["top_performers"][0] if g["top_performers"] else f"Winner: {g['winner']}"),
        ])

    per_slide = max(total_duration / len(slide_texts), 3)
    image_clips = []
    for i, lines in enumerate(slide_texts):
        img_path = os.path.join(out_dir, f"{league_key}_{date_str}_slide{i}.png")
        _make_slide(lines, league["color"], img_path)
        clip = ImageClip(img_path).set_duration(per_slide)
        image_clips.append(clip)

    video = concatenate_videoclips(image_clips, method="compose")
    video = video.set_duration(total_duration)

    # 3) Audio mix: narration + optional music bed (ducked under narration)
    audio_tracks = [narration_clip.set_duration(total_duration)]
    music_path = DEFAULT_MUSIC.get(league_key)
    if music_path and os.path.exists(music_path):
        music = AudioFileClip(music_path).volumex(0.15).fx(afx.audio_loop, duration=total_duration)
        audio_tracks.append(music)

    final_audio = CompositeAudioClip(audio_tracks).set_duration(total_duration)
    video = video.set_audio(final_audio)
    video = video.set_fps(VIDEO_FPS)

    out_path = os.path.join(out_dir, f"{league_key}_{date_str}_recap.mp4")
    video.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=VIDEO_FPS, verbose=False, logger=None)

    return out_path
