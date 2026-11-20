#!/usr/bin/env python3
"""Delete arrow glyphs and photo overlay controls at source, retain swipe click targets."""
from pathlib import Path
import re
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
# Preserve existing button IDs, so swipe navigation can still click them.
for ident in ("memBookPrev","memBookNext"):
 pattern=r'(<button\b[^>]*\bid="'+ident+r'"[^>]*>)(.*?)(</button>)'
 matches=list(re.finditer(pattern,s,re.S))
 assert len(matches)==1,(ident,len(matches))
 s=re.sub(pattern,lambda m:m.group(1)+m.group(3),s,count=1,flags=re.S)
# Remove the actual overlay elements, not merely their appearance.
s,n=re.subn(r'<div class="v4-photo-page-turns">\s*<button[^>]*class="v4-photo-prev"[^>]*>.*?</button>\s*<button[^>]*class="v4-photo-next"[^>]*>.*?</button>\s*</div>','',s,flags=re.S)
assert n==2,("overlay arrows",n)
# Hide empty navigation buttons from the UI while keeping their click listeners.
s=s.replace('</body>','<style id="memories-no-arrow-buttons">#memBookArrows{position:absolute!important;left:-99999px!important;top:-99999px!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important}</style></body>',1)
assert 'id="memBookPrev"' in s and 'id="memBookNext"' in s
assert 'class="v4-photo-prev"' not in s and 'class="v4-photo-next"' not in s
p.write_text(s,encoding="utf-8")
print("PASS: deleted 2 photo arrow overlays and both original arrow glyphs; swipe targets preserved")
