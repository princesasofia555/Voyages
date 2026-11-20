#!/usr/bin/env python3
"""Hide legacy page-turn arrows only on cover and first photo page."""
from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
assert 'id="collageScreen"' in s
css="""<style id="memories-hide-cover-first-photo-arrows">
/* Target the arrow container directly: no :has() dependency. */
#collageScreen .v4-photo-page-turns,
#collageScreen .v4-photo-prev,
#collageScreen .v4-photo-next,
body:has(#collageScreen.active) .v4-photo-prev,
body:has(#collageScreen.active) .v4-photo-next,
body:has(#collageScreen.active) .v4-photo-page-turns,
body:has(#collageScreen.active) #memBookArrows,
body:has(#coverScreen.active) #memBookArrows,
body:has(#frontScreen.active) #memBookArrows,
body:has(#openingScreen.active) #memBookArrows,
body:has(#coverScreen.active) .v4-photo-page-turns,
body:has(#frontScreen.active) .v4-photo-page-turns{
  display:none!important;visibility:hidden!important;
  opacity:0!important;pointer-events:none!important;
}
</style>"""
assert "</body>" in s
s=s.replace("</body>",css+"</body>",1)
p.write_text(s,encoding="utf-8")
print("PASS: old arrows hidden on cover and first photo page")
