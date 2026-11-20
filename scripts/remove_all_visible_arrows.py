#!/usr/bin/env python3
"""Remove legacy page-turn arrow UI everywhere; retain hidden buttons for swipe events."""
from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
for key in ('id="memBookPrev"','id="memBookNext"','id="memBookArrows"'):
 assert key in s,key
css="""<style id="memories-no-visible-page-arrows">
/* The swipe handler still calls the hidden buttons programmatically. */
#memBookArrows,
#memBookPrev,
#memBookNext,
.v4-photo-page-turns,
.v4-photo-prev,
.v4-photo-next {
 display:none!important;
 visibility:hidden!important;
 opacity:0!important;
 pointer-events:none!important;
}
</style>"""
assert '</body>' in s
s=s.replace('</body>',css+'</body>',1)
p.write_text(s,encoding="utf-8")
print("PASS: both global and overlay navigation arrows hidden")
