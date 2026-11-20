#!/usr/bin/env python3
"""Edit globe list markup at its source: category icons and close buttons."""
from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
# Both country and grouped-marker lists have the same old colored dot.
old='''<span style="color:${p.kind==='hotel'?'#81b6e0':'#ed718c'};font-size:18px">●</span>'''
old2='''<span style="color:${p.kind==='hotel'?'#81b6e0':'#ed718c'};font-size:20px">●</span>'''
new='''<span aria-hidden="true" style="font-size:18px;flex:none">${p.kind==='hotel'?'📍':'📌'}</span>'''
for target in (old,old2):
 assert s.count(target)==1,('globe category dot',s.count(target))
 s=s.replace(target,new,1)
# A place detail currently has no close button; add one to the actual renderer.
old_detail='''detail.innerHTML=`<h3>${p.kind==='hotel'?'📍':'📌'} ${esc(p.name)}</h3><p>'''
new_detail='''detail.innerHTML=`<div style="display:flex;align-items:center;justify-content:space-between;gap:10px"><h3 style="margin:0">${p.kind==='hotel'?'📍':'📌'} ${esc(p.name)}</h3><button type="button" id="closeMapVisit" aria-label="Close details" style="border:1px solid #a77d5d;border-radius:16px;background:#421829;color:#fff;padding:5px 12px">✕</button></div><p>'''
assert s.count(old_detail)==1,('visit details renderer',s.count(old_detail))
s=s.replace(old_detail,new_detail,1)
anchor='''<div style="text-align:left;max-width:420px;margin:auto">${details||'<p>No dates recorded.</p>'}</div>`;
}'''
replacement='''<div style="text-align:left;max-width:420px;margin:auto">${details||'<p>No dates recorded.</p>'}</div>`;
 detail.querySelector('#closeMapVisit').onclick=()=>{detail.textContent='Tap a marker or numbered group to explore your memories.'};
}'''
assert s.count(anchor)==1,('visit detail close hook',s.count(anchor))
s=s.replace(anchor,replacement,1)
assert s.count('id="closeCountryList"')==1
assert s.count('id="closeGlobeGroup"')==1
assert s.count('id="closeMapVisit"')==1
assert 'font-size:18px">●' not in s and 'font-size:20px">●' not in s
p.write_text(s,encoding='utf-8')
print('PASS: globe country/group dots replaced with matching restaurant/hotel icons')
print('PASS: country/group close buttons preserved and place-detail close button added')
