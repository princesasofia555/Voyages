#!/usr/bin/env python3
"""Reject an APK unless all three photo pages contain the user-approved artwork."""
from pathlib import Path
from html.parser import HTMLParser
import base64, hashlib, re

APPROVED_DECOR_SHA256 = "b13047610f7bfe0cf4a09308562d6e1c94fcc4834659a326f5f9ca9571e40286"
html = Path("app/src/main/assets/index.html").read_text(encoding="utf-8")
class Frames(HTMLParser):
    def __init__(self):
        super().__init__()
        self.frames = {}
    def handle_starttag(self, tag, attrs):
        if tag == "iframe":
            attrs = dict(attrs)
            if attrs.get("id", "").startswith("freeCollageFrame"):
                self.frames[attrs["id"]] = attrs.get("srcdoc", "")
parser = Frames()
parser.feed(html)
expected = {"freeCollageFrame", "freeCollageFrame2", "freeCollageFrame3"}
assert set(parser.frames) == expected, f"Expected exactly three photo pages: {parser.frames.keys()}"
for name, doc in parser.frames.items():
    match = re.search(r'<img id="decor"[^>]*base64,([^" ]+)', doc)
    assert match, f"{name}: missing original decor image"
    digest = hashlib.sha256(base64.b64decode(match.group(1))).hexdigest()
    assert digest == APPROVED_DECOR_SHA256, f"{name}: decor is not the approved rose/petal version: {digest}"
    assert "Add Photo" in doc and "Delete Photo" in doc and "Done" in doc, f"{name}: photo toolbar missing"
print("PASS: all three photo pages use exactly the approved artwork and toolbar")
