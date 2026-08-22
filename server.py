#!/usr/bin/env python3
"""
Ehsaas Music Server
===================
Scans audio/<theme>/ folders automatically and serves the
track list as JSON at GET /tracks.  All static files
(HTML, CSS, JS, images, audio) are served from the same
directory.

HOW TO RUN
----------
  python3 server.py

Then open:  http://localhost:3000

HOW TO ADD SONGS
----------------
1. Drop any .mp3 / .m4a / .ogg / .flac / .wav file into
   the matching folder:

     audio/midnight/
     audio/priyanka/
     audio/dawn/
     audio/forest/
     audio/sepia/
     audio/ocean/

2. Refresh the browser — the song appears automatically.
   No code changes needed, ever.

REQUIREMENTS
------------
Python 3.6+  (already installed on this Mac)
No external packages needed.
"""

import http.server
import json
import os
import urllib.parse
from pathlib import Path

PORT       = 3000
ROOT       = Path(__file__).parent.resolve()   # the "web photo" folder
AUDIO_ROOT = ROOT / "audio"

THEMES = ["midnight", "dawn", "forest", "sepia", "ocean", "priyanka"]

AUDIO_EXTS = {".mp3", ".m4a", ".ogg", ".flac", ".wav"}

# Default album art per theme
THEME_THUMBS = {
    "midnight" : "bg1.png",
    "forest"   : "bg2.png",
    "priyanka" : "image.png",
}

MIME_TYPES = {
    ".html"  : "text/html; charset=utf-8",
    ".css"   : "text/css",
    ".js"    : "application/javascript",
    ".json"  : "application/json",
    ".png"   : "image/png",
    ".jpg"   : "image/jpeg",
    ".jpeg"  : "image/jpeg",
    ".gif"   : "image/gif",
    ".webp"  : "image/webp",
    ".svg"   : "image/svg+xml",
    ".ico"   : "image/x-icon",
    ".mp3"   : "audio/mpeg",
    ".m4a"   : "audio/mp4",
    ".ogg"   : "audio/ogg",
    ".flac"  : "audio/flac",
    ".wav"   : "audio/wav",
    ".woff"  : "font/woff",
    ".woff2" : "font/woff2",
    ".ttf"   : "font/ttf",
}


def scan_tracks():
    """
    Walk every audio/<theme>/ folder and return a dict:
    {
      "midnight": [ {id, name, artist, album, duration, src, thumb}, … ],
      "priyanka": [ … ],
      …
    }

    - src uses forward slashes and is URL-percent-encoded so
      filenames with spaces (e.g. "I Think They Call This Love.mp3")
      load correctly in the browser's <audio> element.
    - Called fresh on every /tracks request — no server restart needed.
    """
    result  = {}
    next_id = 1

    for theme in THEMES:
        theme_dir = AUDIO_ROOT / theme
        tracks    = []

        if not theme_dir.is_dir():
            result[theme] = tracks
            continue

        # Collect audio files and sort naturally (handles numbers in names)
        files = sorted(
            [f for f in theme_dir.iterdir()
             if f.is_file() and f.suffix.lower() in AUDIO_EXTS],
            key=lambda f: f.name.lower()
        )

        for f in files:
            stem = f.stem  # filename without extension

            # Make a readable display name:
            # "I_Think_They_Call_This_Love" → "I Think They Call This Love"
            name = stem.replace("-", " ").replace("_", " ")
            # collapse multiple spaces
            name = " ".join(name.split())

            # URL-encode the filename so spaces become %20
            # e.g.  "I Think They Call This Love.mp3"
            #    →  "audio/priyanka/I%20Think%20They%20Call%20This%20Love.mp3"
            encoded_filename = urllib.parse.quote(f.name)
            src = f"audio/{theme}/{encoded_filename}"

            thumb = THEME_THUMBS.get(theme, "bg1.png")

            tracks.append({
                "id"      : next_id,
                "name"    : name,
                "artist"  : "",        # filled by <audio> loadedmetadata if needed
                "album"   : "",
                "duration": "",        # filled by <audio> loadedmetadata
                "src"     : src,
                "thumb"   : thumb,
            })
            next_id += 1

        result[theme] = tracks

    return result


class EhsaasHandler(http.server.BaseHTTPRequestHandler):

    # Silence the default per-request log line; we print our own
    def log_message(self, fmt, *args):
        pass

    def do_HEAD(self):
        """Support HEAD requests — browsers use these to check audio file size."""
        self._handle(head_only=True)

    def do_GET(self):
        self._handle(head_only=False)

    def _handle(self, head_only=False):
        parsed   = urllib.parse.urlparse(self.path)
        pathname = urllib.parse.unquote(parsed.path)

        # ── /tracks ── return fresh JSON scan ──────────
        if pathname == "/tracks":
            data = scan_tracks()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            total = sum(len(v) for v in data.values())
            print(f"  [/tracks]  {total} tracks found across {len(THEMES)} themes")
            self.send_response(200)
            self.send_header("Content-Type",  "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control",  "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if not head_only:
                self.wfile.write(body)
            return

        # ── Static files ────────────────────────────────
        if pathname == "/":
            pathname = "/index.html"

        # Resolve the real path; prevent path traversal
        try:
            file_path = (ROOT / pathname.lstrip("/")).resolve()
        except Exception:
            self.send_error(400)
            return

        if not str(file_path).startswith(str(ROOT)):
            self.send_error(403, "Forbidden")
            return

        if not file_path.is_file():
            self.send_error(404, f"Not found: {pathname}")
            return

        suffix    = file_path.suffix.lower()
        mime_type = MIME_TYPES.get(suffix, "application/octet-stream")

        try:
            with open(file_path, "rb") as fh:
                data = fh.read()
        except OSError:
            self.send_error(500)
            return

        self.send_response(200)
        self.send_header("Content-Type",   mime_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head_only:
            self.wfile.write(data)


def main():
    # Print startup info
    print()
    print("  ♫  Ehsaas Music Server")
    print(f"  →  http://localhost:{PORT}")
    print()
    print("  Drop MP3s into any audio/<theme>/ folder,")
    print("  then refresh the browser — songs appear automatically.")
    print()
    print("  Current tracks:")
    tracks = scan_tracks()
    for theme, t_list in tracks.items():
        files_label = f"{len(t_list)} track{'s' if len(t_list) != 1 else ''}"
        print(f"    audio/{theme}/  —  {files_label}")
        for t in t_list:
            print(f"      • {t['name']}")
    print()
    print("  Press Ctrl+C to stop.")
    print()

    server = http.server.HTTPServer(("", PORT), EhsaasHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    main()
