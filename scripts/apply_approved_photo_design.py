#!/usr/bin/env python3
"""Apply the approved three-page artwork to the Android app without replacing its data or UI."""
from pathlib import Path
import hashlib, html, lzma, re
from html.parser import HTMLParser

source = Path("app/src/main/assets/Memories_3_Pages_Design_Valide_PREPARATION.html.xz")
target = Path("app/src/main/assets/index.html")
assert source.is_file(), "Upload the approved .html.xz file to app/src/main/assets/ first"
reference = lzma.decompress(source.read_bytes()).decode("utf-8")
app = target.read_text(encoding="utf-8")
class Frames(HTMLParser):
    def __init__(self):
        super().__init__()
        self.frames = {}
    def handle_starttag(self, tag, attrs):
        if tag == "iframe":
            attrs = dict(attrs)
            name = attrs.get("id")
            if name in ("freeCollageFrame", "freeCollageFrame2", "freeCollageFrame3"):
                self.frames[name] = attrs.get("srcdoc", "")
ref = Frames()
ref.feed(reference)
assert len(ref.frames) == 3, "Approved reference must contain all three pages"
for frame_id, approved in ref.frames.items():
    pattern = r'(<iframe\b[^>]*?\bid="' + frame_id + r'"[^>]*?\bsrcdoc=")(.*?)(")'
    matches = list(re.finditer(pattern, app, re.DOTALL))
    assert len(matches) == 1, f"Missing or duplicate {frame_id}"
    original = html.unescape(matches[0].group(2))
    assert "MemoriesV" in original and "Add Photo" in original, f"{frame_id} is not a collage"
    app = app[:matches[0].start(2)] + html.escape(approved, quote=True) + app[matches[0].end(2):]
    print(frame_id, hashlib.sha256(approved.encode()).hexdigest())
target.write_text(app, encoding="utf-8")
print("Applied approved artwork to all three Android collage pages; app navigation and data untouched")
