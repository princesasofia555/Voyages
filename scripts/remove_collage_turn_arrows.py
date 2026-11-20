#!/usr/bin/env python3
"""Remove the overlooked collageTurnPrev/Next buttons from the first photo page."""
from pathlib import Path
import re
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
for ident in ("collageTurnPrev","collageTurnNext"):
 pat=r'(<button\b[^>]*\bid="'+ident+r'"[^>]*>)(.*?)(</button>)'
 matches=list(re.finditer(pat,s,re.S))
 assert len(matches)==1,(ident,len(matches))
 s=re.sub(pat,lambda m:m.group(1)+m.group(3),s,count=1,flags=re.S)
# Existing click listeners require the buttons, so retain them as invisible navigation targets.
css='<style id="memories-remove-collage-turn-controls">#collageTurnPrev,#collageTurnNext{display:none!important;visibility:hidden!important;pointer-events:none!important}</style>'
assert '</body>' in s
s=s.replace('</body>',css+'</body>',1)
p.write_text(s,encoding="utf-8")
print("PASS: first photo page collageTurnPrev and collageTurnNext arrow glyphs removed")
