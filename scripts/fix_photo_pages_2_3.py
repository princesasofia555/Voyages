#!/usr/bin/env python3
"""Repair ONLY photo pages 2 and 3 using the already-approved first-page layout."""
from pathlib import Path
import re, html
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
ids=["freeCollageFrame","freeCollageFrame2","freeCollageFrame3"]
docs={}
for fid in ids:
    pat=r'(<iframe\b[^>]*?\bid="'+fid+r'"[^>]*?\bsrcdoc=")(.*?)(")'
    found=list(re.finditer(pat,s,re.S))
    assert len(found)==1,(fid,len(found))
    docs[fid]=html.unescape(found[0].group(2))
# Pages 2 and 3 inherited obsolete pseudo-element art masks that split the
# border and flowers into two pieces. Remove ONLY this legacy block.
legacy=re.compile(r'\n#page::before,#page::after\{.*?\n#page::after\{left:0;bottom:0;.*?\}\n',re.S)
assert not legacy.search(docs["freeCollageFrame"]), "First approved page unexpectedly has legacy masks"
for fid in ids[1:]:
    doc=docs[fid]
    doc,n=legacy.subn("\n",doc,count=1)
    assert n==1,(fid,"Expected exactly one obsolete collage mask block")
    # No change to the user-approved image, independent photo storage,
    # page navigation logic or user photos.
    pat=r'(<iframe\b[^>]*?\bid="'+fid+r'"[^>]*?\bsrcdoc=")(.*?)(")'
    m=re.search(pat,s,re.S)
    s=s[:m.start(2)]+html.escape(doc,quote=True)+s[m.end(2):]
# Remove the distracting side-arrow visuals on photo pages only.
s += """
<style id="memories-hide-photo-arrows-v502">
body:has(#collageScreen.active) .v4-photo-page-turns button,
body:has(#collage2Screen.active) .v4-photo-page-turns button,
body:has(#collage3Screen.active) .v4-photo-page-turns button{
 background:transparent!important;border:0!important;color:transparent!important;
 box-shadow:none!important;opacity:0!important;
}
</style>
"""
assert 'id="collage2Screen"' in s and 'id="collage3Screen"' in s
p.write_text(s,encoding="utf-8")
print("PASS: pages 2 and 3 legacy masks removed; first page left unchanged")
