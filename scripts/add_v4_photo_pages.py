#!/usr/bin/env python3
"""Add two independent photo collage pages without changing the approved design."""
from pathlib import Path
import re

path = Path("app/src/main/assets/index.html")
html = path.read_text(encoding="utf-8")
start = html.index('<section id="collageScreen"')
end = html.index('</section>', start) + len('</section>')
original = html[start:end]
assert 'id="freeCollageFrame"' in original
assert 'MemoriesV3FreeCollage' in original
assert "const pages=['collage','list','hotels','map','end'];" in html
assert "if(page==='collage')" in html

# Keep the approved artwork in front of movable photographs on all three pages.
# The iframe contains HTML-escaped CSS. Reuse its own background artwork:
# no replacement drawing or image, and no change to stored photo coordinates.
foreground_css = """
#page::before,#page::after{
 content:'';position:absolute;pointer-events:none;z-index:9000;
 background-image:inherit;background-repeat:no-repeat;
 background-size:100vw 100dvh;
}
#page::before{left:0;top:0;width:55%;height:26%;background-position:left top}
#page::after{left:0;bottom:0;width:100%;height:27%;background-position:left bottom}
"""
assert original.count('&lt;/style&gt;') == 1, 'Collage iframe style marker missing'
original=original.replace('&lt;/style&gt;',foreground_css+'&lt;/style&gt;',1)
assert original.count('#page::before')==1
new_pages = []
for number in (2, 3):
    clone = original.replace('id="collageScreen"', f'id="collage{number}Screen"')
    clone = clone.replace('id="freeCollageFrame"', f'id="freeCollageFrame{number}"')
    clone = clone.replace('MemoriesV3FreeCollage', f'MemoriesV4FreeCollage{number}')
    clone = clone.replace('Free photo collage', f'Free photo collage page {number}')
    new_pages.append(clone)
html = html[:end] + ''.join(new_pages) + html[end:]
html = html.replace(
    "const pages=['collage','list','hotels','map','end'];",
    "const pages=['collage','collage2','collage3','list','hotels','map','end'];",
    1
)
html = html.replace(
    "if(page==='collage'){document.querySelectorAll('.screen').forEach(el=>el.classList.remove('active'));document.getElementById('collageScreen').classList.add('active');sync();window.scrollTo(0,0);return;}",
    "if(page==='collage'||page==='collage2'||page==='collage3'){document.querySelectorAll('.screen').forEach(el=>el.classList.remove('active'));document.getElementById(page+'Screen').classList.add('active');sync();window.scrollTo(0,0);return;}",
    1
)
html = html.replace(
    "document.getElementById('endScreen').classList.remove('active');document.getElementById('collageScreen').classList.remove('active');",
    "document.getElementById('endScreen').classList.remove('active');['collage','collage2','collage3'].forEach(p=>document.getElementById(p+'Screen').classList.remove('active'));",
    1
)
html = html.replace(
    "#globeScreen,#collageScreen,#listScreen,#hotelScreen,#mapScreen,#endScreen",
    "#globeScreen,#collageScreen,#collage2Screen,#collage3Screen,#listScreen,#hotelScreen,#mapScreen,#endScreen",
    1
)
# The collage is an iframe: it captures touches, so parent document navigation
# cannot receive taps on the page. Add explicit accessible turn controls above it.
for page in ("collage", "collage2", "collage3"):
    marker = f'<section id="{page}Screen"'
    start = html.index(marker)
    end = html.index('</section>', start)
    controls = (
        '<div class="v4-photo-page-turns">'
        '<button type="button" class="v4-photo-prev" aria-label="Previous page">‹</button>'
        '<button type="button" class="v4-photo-next" aria-label="Next page">›</button>'
        '</div>'
    )
    html = html[:end] + controls + html[end:]
# Bind overlay controls to the already-existing book navigation.
overlay_script = """<script id="v4-photo-navigation">
document.addEventListener('click',function(e){
  const prev=e.target.closest('.v4-photo-prev');
  const next=e.target.closest('.v4-photo-next');
  if(!prev&&!next)return;
  e.preventDefault();e.stopPropagation();
  document.getElementById(prev?'memBookPrev':'memBookNext').click();
},true);
</script>
<style id="v4-photo-navigation-style">
#collageScreen,#collage2Screen,#collage3Screen{position:relative!important}\n/* Hide original arrows only on photo pages; keep the new overlay arrows. */\nbody:has(#collageScreen.active) #memBookArrows,\nbody:has(#collage2Screen.active) #memBookArrows,\nbody:has(#collage3Screen.active) #memBookArrows{opacity:0!important;pointer-events:none!important}\n/* The original iframe also renders its own left/right navigation; hide only those\n   on photo pages, leaving V4's overlay controls usable. */\n#collageScreen .v4-photo-page-turns ~ .old-arrow,\n#collage2Screen .v4-photo-page-turns ~ .old-arrow,\n#collage3Screen .v4-photo-page-turns ~ .old-arrow{display:none!important}
.v4-photo-page-turns{position:absolute;z-index:100;inset:0;pointer-events:none}
.v4-photo-page-turns button{pointer-events:auto;position:absolute;top:48%;width:42px;height:76px;
 border:0;border-radius:9px;background:#431327a8;color:#ffe7a0;font-size:35px}
.v4-photo-prev{left:0}.v4-photo-next{right:0}
</style>"""
html = html.replace('</body>', overlay_script+'</body>', 1)
# Reposition the toolbar INSIDE each iframe srcdoc. The HTML contains the CSS\n# as an HTML-escaped attribute, but the CSS selector remains plain text.\nold_toolbar = '.toolbar{position:absolute;top:3.2%;right:5%;'\nnew_toolbar = '.toolbar{position:absolute;top:3.2%;right:16%;'\nassert html.count(old_toolbar) == 3, 'Expected three photo-page toolbars'\nhtml = html.replace(old_toolbar, new_toolbar)\n# Disable the obsolete first-page iframe edge click bridge: overlay arrows\n# are the sole navigation controls for all three photo pages.\nhtml = html.replace('id="memories-collage-navigation-bridge"', 'id="memories-collage-navigation-bridge-disabled"')\nbridge_start = html.find('<script id="memories-collage-navigation-bridge-disabled">')\nif bridge_start >= 0:\n    bridge_end = html.index('</script>', bridge_start) + len('</script>')\n    html = html[:bridge_start] + html[bridge_end:]\n# Preserve full-page appearance on new collage screens.
html += """\n<style id="memories-v4-extra-collage-pages">
#collage2Screen,#collage3Screen{padding:0!important;margin:0!important}
#collage2Screen iframe,#collage3Screen iframe{display:block;width:100%;height:100dvh;border:0}
</style>\n"""
assert html.count('id="collage2Screen"') == 1
assert html.count('id="collage3Screen"') == 1
assert 'MemoriesV4FreeCollage2' in html and 'MemoriesV4FreeCollage3' in html
path.write_text(html, encoding="utf-8")
print("V4: 3 photo collage pages with independent IndexedDB storage.")
