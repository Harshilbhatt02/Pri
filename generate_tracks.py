#!/usr/bin/env python3
"""
Ehsaas — generate_tracks.py
============================
Scans all audio/<theme>/ folders and writes tracks.json.

RUN THIS every time you add or remove MP3 files:
    python3 generate_tracks.py

Then commit and push to GitHub — songs update on GitHub Pages too.

Supported formats: .mp3  .m4a  .ogg  .flac  .wav
"""

import json
import os
import urllib.parse
from pathlib import Path

ROOT       = Path(__file__).parent.resolve()
AUDIO_ROOT = ROOT / "audio"
OUTPUT     = ROOT / "tracks.json"

THEMES = ["midnight", "dawn", "forest", "sepia", "ocean", "priyanka"]

AUDIO_EXTS = {".mp3", ".m4a", ".ogg", ".flac", ".wav"}

THEME_THUMBS = {
    "midnight" : "bg1.png",
    "forest"   : "bg2.png",
    "priyanka" : "image.png",
}

def build_tracks():
    result  = {}
    next_id = 1

    for theme in THEMES:
        theme_dir = AUDIO_ROOT / theme
        tracks    = []

        if theme_dir.is_dir():
            files = sorted(
                [f for f in theme_dir.iterdir()
                 if f.is_file() and f.suffix.lower() in AUDIO_EXTS],
                key=lambda f: f.name.lower()
            )

            for f in files:
                name = f.stem.replace("-", " ").replace("_", " ")
                name = " ".join(name.split())

                # URL-encode spaces so the browser's <audio> element
                # can load files with spaces in their names
                encoded_name = urllib.parse.quote(f.name)
                src = f"audio/{theme}/{encoded_name}"

                thumb = THEME_THUMBS.get(theme, "bg1.png")

                tracks.append({
                    "id"      : next_id,
                    "name"    : name,
                    "artist"  : "",
                    "album"   : "",
                    "duration": "",
                    "src"     : src,
                    "thumb"   : thumb,
                })
                next_id += 1

        result[theme] = tracks

    return result


def main():
    print()
    print("  Ehsaas — scanning audio folders...")
    print()

    tracks = build_tracks()

    # Write tracks.json
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        json.dump(tracks, fh, ensure_ascii=False, indent=2)

    # Print summary
    total = sum(len(v) for v in tracks.values())
    print(f"  tracks.json updated — {total} track(s) found")
    print()
    for theme, t_list in tracks.items():
        label = f"{len(t_list)} track{'s' if len(t_list) != 1 else ''}"
        print(f"    audio/{theme}/  —  {label}")
        for t in t_list:
            print(f"      • {t['name']}")
    print()
    print("  Done! Now:")
    print("  • Locally : open index.html with python3 server.py")
    print("  • GitHub  : git add tracks.json && git commit -m 'update tracks' && git push")
    print()


if __name__ == "__main__":
    main()
