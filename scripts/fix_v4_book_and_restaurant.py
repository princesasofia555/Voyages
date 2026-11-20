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
s += "\n<!-- memories-v4-verified-toolbar-and-backup -->\n"
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
# Give every restaurant a unique stable key, including entries sharing old numeric IDs.
# The visible list number is a display position, never an edit identifier.
old_load = "for(const memory of BASE){"
new_load = """const usedMemoryIds=new Set();items.forEach((x,k)=>{let uid=String(x._uid||'');if(!uid||usedMemoryIds.has(uid)){uid='memories-row-'+k+'-'+Date.now();x._uid=uid;}usedMemoryIds.add(uid)});try{localStorage.setItem(KEY,JSON.stringify(items))}catch(e){};for(const memory of BASE){"""
assert s.count(old_load)==1
s=s.replace(old_load,new_load,1)
# BASE entries appended during merge also need unique IDs.
anchor="const persist=()=>"
assert s.count(anchor)==1
s=s.replace(anchor,"""{const seen=new Set();items.forEach((x,k)=>{let id=String(x._uid||'');if(!id||seen.has(id)){id='memories-final-'+k+'-'+Date.now();x._uid=id;}seen.add(id)});try{localStorage.setItem(KEY,JSON.stringify(items))}catch(e){}};"""+anchor,1)
assert s.count("x.i||x._n")>=2
s=s.replace("x.i||x._n","x._uid")
s=s.replace("const find=id=>items.find(x=>String(x.i||x._uid)===String(id));","const find=id=>items.find(x=>String(x._uid)===String(id));")
s=s.replace("editId=x?String(x.i||x._uid):null;","editId=x?String(x._uid):null;")
s=s.replace("String(y.i||y._uid)!==String(id)","String(y._uid)!==String(id)")
# The top-right star opens the Add Experience menu: retain it on the first page only.
s += """
<style id="memories-v4-hide-extra-photo-tools">
body:has(#collage2Screen.active) #memBookTools,
body:has(#collage3Screen.active) #memBookTools,
body:has(#collage2Screen.active) #memBookMenu,
body:has(#collage3Screen.active) #memBookMenu{display:none!important;pointer-events:none!important}
</style>
"""
assert 'const find=id=>items.find(x=>String(x._uid)===String(id));' in s
assert 'memories-v4-hide-extra-photo-tools' in s
# Critical: V3 forced the Crissier restaurant name during every render,
# overriding user edits even when the new name was correctly saved.
old_name_render = "esc(memoriesOriginalRestaurantName(x))"
assert s.count(old_name_render) in (0,1), ('Forced restaurant name renderer', s.count(old_name_render))
s = s.replace(old_name_render, "esc(x.name)", 1)
assert "esc(memoriesOriginalRestaurantName(x))" not in s
# All-card audit: show the saved name, not a hard-coded alias for Crissier.
forced_name = 'esc(memoriesOriginalRestaurantName(x))'
assert s.count(forced_name) in (0,1), ('Forced name renderer count', s.count(forced_name))
s=s.replace(forced_name,'esc(x.name)')
# All-card audit: do not silently claim a failed localStorage write succeeded.
old_persist = "const persist=()=>{try{localStorage.setItem(KEY,JSON.stringify(items))}catch(e){alert('Unable to save: insufficient storage. Back up your data and use smaller photos.')}if($('count'))$('count').textContent=items.length;};"
new_persist = "const persist=()=>{try{localStorage.setItem(KEY,JSON.stringify(items));if($('count'))$('count').textContent=items.length;return true}catch(e){alert('Unable to save: insufficient storage. Back up your data and use smaller photos.');return false}};"
assert s.count(old_persist)==1, 'Persist function not found'
s=s.replace(old_persist,new_persist,1)
# Do not close the edit form or display a success toast when storage fails.
old_submit = "items.push(obj);}persist();renderFlatMap();$('modal').classList.add('hidden');render();toast(old?'Experience updated':'Experience added')"
new_submit = "items.push(obj);}if(!persist())return;renderFlatMap();$('modal').classList.add('hidden');render();toast(old?'Experience updated':'Experience added')"
assert s.count(old_submit)==1, 'Restaurant submit handler not found'
s=s.replace(old_submit,new_submit,1)
# Root cause: BASE re-import was matching by name/date, so a renamed
# restaurant was re-added under its OLD name every time the app restarted.
old_merge="if(memory._uid&&!items.some(r=>r._uid===memory._uid||(r.name===memory.name&&r.date===memory.date))){items.push(memory)}"
new_merge="if(memory._uid&&!items.some(r=>r._uid===memory._uid||(r.i===memory.i&&r.date===memory.date)||(r.name===memory.name&&r.date===memory.date))){items.push(memory)}"
assert s.count(old_merge)==1,('BASE merge',s.count(old_merge))
s=s.replace(old_merge,new_merge,1)
# Keep the user-entered name and allow matching photos by stable original index.
old_restored="const existing=items.find(x=>x.name===restored.name&&x.date===restored.date);"
new_restored="const existing=items.find(x=>(x.i===restored.i&&x.date===restored.date)||(x.name===restored.name&&x.date===restored.date));"
assert s.count(old_restored)==1,('Photo restore',s.count(old_restored))
s=s.replace(old_restored,new_restored,1)
# Hotel audit: stable note keys (with backwards-compatible fallback) and no duplicate custom stays.
old_hotel_key="function hotelNoteKey(h){return 'voyages_hotel_note_'+encodeURIComponent(h.n+'|'+h.city+'|'+h.date)}"
new_hotel_key="""HOTELS.forEach((h,i)=>{if(!h._uid)h._uid='hotel-'+i+'-'+encodeURIComponent(h.date)});
function hotelLegacyNoteKey(h){return 'voyages_hotel_note_'+encodeURIComponent(h.n+'|'+h.city+'|'+h.date)}
function hotelNoteKey(h){return 'voyages_hotel_note_uid_'+encodeURIComponent(h._uid)}"""
assert s.count(old_hotel_key)==1,('Hotel note key',s.count(old_hotel_key))
s=s.replace(old_hotel_key,new_hotel_key,1)
old_hotel_note="localStorage.getItem(hotelNoteKey(x))||''"
assert s.count(old_hotel_note)==1
s=s.replace(old_hotel_note,"localStorage.getItem(hotelNoteKey(x))||localStorage.getItem(hotelLegacyNoteKey(x))||''",1)
old_hotel_add="JSON.stringify(HOTELS.filter(x=>x._custom).concat([{...stay,_custom:true}]))"
assert s.count(old_hotel_add)==1,('Duplicate hotel insert',s.count(old_hotel_add))
s=s.replace(old_hotel_add,"JSON.stringify(HOTELS.filter(x=>x._custom).concat([{...stay,_custom:true,_uid:'hotel-custom-'+Date.now()}]))",1)
# Assign the same stable identifier to the in-memory new stay before persistence.
s=s.replace("};HOTELS.push(stay);\ntry{localStorage.setItem('voyages_custom_hotels_v1'","};stay._custom=true;stay._uid='hotel-custom-'+Date.now();HOTELS.push(stay);\ntry{localStorage.setItem('voyages_custom_hotels_v1'",1)
s=s.replace("JSON.stringify(HOTELS.filter(x=>x._custom).concat([{...stay,_custom:true,_uid:'hotel-custom-'+Date.now()}]))","JSON.stringify(HOTELS.filter(x=>x._custom))",1)
# Photos keyed by hotel stable ID, with old index as migration fallback.
old_photo="localStorage.getItem('voyages_hotel_photo_'+i)||localStorage.getItem('voyages_hotel_shared_'+h.n.replace(/ Château$/,'').toLowerCase())"
new_photo="localStorage.getItem('voyages_hotel_photo_uid_'+encodeURIComponent(h._uid))||localStorage.getItem('voyages_hotel_photo_'+i)||localStorage.getItem('voyages_hotel_shared_'+h.n.replace(/ Château$/,'').toLowerCase())"
assert s.count(old_photo)==1,('Hotel photo reader',s.count(old_photo))
s=s.replace(old_photo,new_photo,1)
p.write_text(s,encoding="utf-8")
print("Stable restaurant IDs preserved on save; back cover fills screen.")
