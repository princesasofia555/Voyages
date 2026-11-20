#!/usr/bin/env python3
"""Hide visible arrows on the actual Memories cover; preserve swipe and tap navigation."""
from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
assert 'id="memoriesCover"' in s
assert 'id="memBookArrows"' in s
patch="""<style id="memories-cover-arrow-removal">
/* Cover is the #memoriesCover element, not #coverScreen. */
body:has(#memoriesCover:not(.is-hidden)) #memBookArrows,
body:has(#memoriesCover:not(.is-hidden)) .v4-photo-page-turns {
 display:none!important;visibility:hidden!important;pointer-events:none!important;
}
</style>
<script id="memories-cover-arrow-sync">
(function(){
 const cover=document.getElementById('memoriesCover');
 const arrows=document.getElementById('memBookArrows');
 if(!cover||!arrows)return;
 function sync(){
  const shown=!cover.classList.contains('is-hidden') && getComputedStyle(cover).display!=='none';
  arrows.style.setProperty('display',shown?'none':'','important');
 }
 new MutationObserver(sync).observe(cover,{attributes:true,attributeFilter:['class','style']});
 sync();
})();
</script>"""
assert '</body>' in s
s=s.replace('</body>',patch+'</body>',1)
p.write_text(s,encoding="utf-8")
print("PASS: cover arrows hidden using real cover element and class")
