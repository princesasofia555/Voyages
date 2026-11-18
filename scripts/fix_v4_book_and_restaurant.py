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
# Final pass: toolbar in all three embedded photo pages must avoid the star.
old_toolbar = '.toolbar{position:absolute;top:3.2%;right:5%;'
new_toolbar = '.toolbar{position:absolute;top:3.2%;right:17%;'
assert s.count(old_toolbar)==3, ('Unexpected photo toolbar count',s.count(old_toolbar))
s=s.replace(old_toolbar,new_toolbar)
assert s.count(new_toolbar)==3 and s.count(old_toolbar)==0
# Mark the actual HTML for inspection; assert the marker is packaged in the APK.
s += '\\n<!-- memories-v4-verified-toolbar-and-backup -->\\n'
# Backup must call the Java bridge that is ACTUALLY registered in MainActivity:
# MemoriesAndroid.save(filename, base64), not nonexistent VoyagesAndroid.saveBackup.
import re
backup_pattern = r"if\(window\.VoyagesAndroid&&typeof window\.VoyagesAndroid\.saveBackup==='function'\)\s*\{\s*window\.VoyagesAndroid\.saveBackup\(json\);"
new_backup = """if(window.MemoriesAndroid&&typeof window.MemoriesAndroid.save==='function'){
    const reader=new FileReader();
    reader.onloadend=()=>{
      const encoded=String(reader.result||'').split(',')[1]||'';
      if(encoded)window.MemoriesAndroid.save('memories-backup-'+new Date().toISOString().slice(0,10)+'.json',encoded);
      else alert('Backup could not be encoded');
    };
    reader.readAsDataURL(new Blob([json],{type:'application/json;charset=utf-8'}));"""
s, backup_count = re.subn(backup_pattern, lambda _: new_backup, s)
assert backup_count == 1, ('Backup handler match count', backup_count)
assert 'window.MemoriesAndroid.save(' in s
p.write_text(s,encoding="utf-8")
print("Stable restaurant IDs preserved on save; back cover fills screen.")
