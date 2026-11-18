"""Repair stable restaurant editing and show the approved back-cover art full screen."""
from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
# Avoid renumbering every restaurant on save: that breaks the stable card IDs
# used for editing, particularly when new experiences were merged.
old="if(old)items=items.map(x=>x===old?obj:x);else items.push(obj);items.forEach((x,i)=>x.i=i+1);persist();"
new="if(old)items=items.map(x=>x===old?obj:x);else {obj.i=Math.max(0,...items.map(x=>Number(x.i)||0))+1;items.push(obj);}persist();"
assert s.count(old)==1,"Expected exact restaurant save handler"
s=s.replace(old,new,1)
# Keep the exact existing artwork, but crop the lower illustrated book-edge
# and fill the entire viewport with the cover rather than displaying the stack.
s += """\n<style id="memories-v4-back-cover-fullscreen">
body.mem-book-mode #endScreen.active{
  position:fixed!important;inset:0!important;width:100vw!important;
  height:100dvh!important;min-height:100dvh!important;
  padding:0!important;margin:0!important;overflow:hidden!important;
}
body.mem-book-mode #endScreen.active #memoriesEndBook{
  position:absolute!important;inset:0!important;
  width:100vw!important;height:100dvh!important;
  min-width:100vw!important;max-width:none!important;
  min-height:100dvh!important;max-height:none!important;
  margin:0!important;padding:0!important;border:0!important;
  border-radius:0!important;box-shadow:none!important;
  background-size:100% 115%!important;
  background-position:center top!important;
  background-repeat:no-repeat!important;
}
body.mem-book-mode #endScreen.active #memoriesEndBook::before,
body.mem-book-mode #endScreen.active #memoriesEndBook::after,
body.mem-book-mode #endScreen.active #memoriesEndBook .book-corner{display:none!important}
</style>\n"""
assert 'memories-v4-back-cover-fullscreen' in s
p.write_text(s,encoding="utf-8")
print("Stable restaurant IDs preserved on save; back cover fills screen.")
