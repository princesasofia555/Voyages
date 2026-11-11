#!/usr/bin/env python3
"""Prepare isolated Memories V2 Android test build without changing approved card layouts."""
from pathlib import Path
import re, base64, io

html_path=Path("app/src/main/assets/index.html")
s=html_path.read_text(encoding="utf-8")
needle="function renderFlatMap(){"
assert s.count(needle)==1, "Unexpected globe source"

# Use coordinates already in the user's offline catalogue; never make network requests.
helper=r'''
function memoriesGeoValid(x){
  return x && x.lat!==null && x.lon!==null &&
    x.lat!==undefined && x.lon!==undefined &&
    Number.isFinite(Number(x.lat)) && Number.isFinite(Number(x.lon)) &&
    Math.abs(Number(x.lat))<=90 && Math.abs(Number(x.lon))<=180;
}
function memoriesCityKey(v){
  return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .toLowerCase().replace(/(?:,?\s+)(?:switzerland|suisse|france|italy|italie|portugal|united kingdom|royaume-uni|germany|allemagne|spain|espagne)$/i,'')
    .split(',')[0].replace(/\([^)]*\)/g,'')
    .replace(/[^a-z0-9]/g,'');
}
function memoriesOfflineCoords(city,name){
  const key=memoriesCityKey(city);
  if(!key)return null;
  const sources=[...BASE,...items,...HOTELS];
  let exactName=sources.find(x=>memoriesGeoValid(x) &&
    String(x.name||x.n||'').toLowerCase()===String(name||'').toLowerCase());
  if(exactName)return {lat:Number(exactName.lat),lon:Number(exactName.lon)};
  const cityMatch=sources.find(x=>memoriesGeoValid(x)&&memoriesCityKey(x.city)===key);
  return cityMatch?{lat:Number(cityMatch.lat),lon:Number(cityMatch.lon)}:null;
}
function memoriesFillMissingCoordinates(){
  let changedRestaurants=false, changedHotels=false;
  for(const x of items){
    if(!memoriesGeoValid(x)){
      const geo=memoriesOfflineCoords(x.city,x.name);
      if(geo){Object.assign(x,geo);changedRestaurants=true;}
    }
  }
  for(const h of HOTELS){
    if(!memoriesGeoValid(h)){
      const geo=memoriesOfflineCoords(h.city,h.n);
      if(geo){Object.assign(h,geo);changedHotels=true;}
    }
  }
  // Persist only successful, grounded matches.
  if(changedRestaurants)persist();
  if(changedHotels){
    try{localStorage.setItem('voyages_custom_hotels_v1',
      JSON.stringify(HOTELS.filter(h=>h._custom)));}catch(e){}
  }
}
'''
s=s.replace(needle,helper+"\n"+"function renderFlatMap(){ memoriesFillMissingCoordinates(); ",1)
assert "function renderFlatMap(){ memoriesFillMissingCoordinates();" in s
# Add inferred geographic coordinates to all *new* records and edits of old records.
hotel="let stay={n,city,date:m+'.'+y,stars:Number($('newHotelStars').value),photo,notes:$('newHotelNotes').value.trim(),lat:null,lon:null};"
assert s.count(hotel)==1
s=s.replace(hotel,hotel.replace("lat:null,lon:null","...((memoriesOfflineCoords(city,n))||{lat:null,lon:null})"),1)
post="if(old)items=items.map(x=>x===old?obj:x);else items.push(obj);"
assert s.count(post)==1
s=s.replace(post,"if(!memoriesGeoValid(obj)){const geo=memoriesOfflineCoords(obj.city,obj.name);if(geo)Object.assign(obj,geo);}"+post,1)
# Ensure map is refreshed after adding/restoring an experience as well.
s=s.replace("persist();$('modal').classList.add('hidden');render();", "persist();renderFlatMap();$('modal').classList.add('hidden');render();",1)
# Only the Selected plaque caption: never alter stars or Bib Gourmand.
caption_before = '`<span class="mic-caption">${esc(enAward(mich))}</span>`'
caption_after = '`<span class="mic-caption">${esc(/selected|sélection|selection/i.test(mich) ? "Selected" : enAward(mich))}</span>`'
assert s.count(caption_before) == 1, "Expected exactly one MICHELIN caption"
s = s.replace(caption_before, caption_after, 1)
# Build-time diagnostic: identify the decorative symbol structure accurately.
caption_pos=s.find('class="mic-caption"')
print("SELECTED_BADGE_SOURCE:",s[max(0,caption_pos-500):caption_pos+250])

# City and country occupy a maximum of two compact lines.
helper = '''
function memoriesLocationTwoLines(raw){
 const location=enPlace(raw||'');
 const countries=/(?:^|[,\s]+)(Switzerland|Suisse|France|Italy|Italie|Portugal|United Kingdom|Royaume-Uni|Germany|Allemagne|Spain|Espagne)\s*$/i;
 const match=location.match(countries);
 const cut=location.lastIndexOf(',');
 const city=match?location.slice(0,match.index).replace(/[,\s]+$/,'').trim():(cut>=0?location.slice(0,cut).trim():location.trim());
 const country=match?match[1]:(cut>=0?location.slice(cut+1).trim():'');
 return '<span class="place-city">'+esc(city)+'</span><span class="place-country">'+esc(country)+'</span>';
}
'''
assert s.count('function renderHotels(){')==1
s=s.replace('function renderHotels(){',helper+'\nfunction renderHotels(){',1)
res_old='<span class="meta">${esc(enPlace(x.city))}</span></span><span class="rest-visit-date"'
hot_old='<span class="meta hotel-location">${esc(enPlace(x.city))}</span><span class="hotel-visit-date">'
assert s.count(res_old)==1, 'restaurant location pattern changed'
assert s.count(hot_old)==1, 'hotel location pattern changed'
res_new='<span class="meta memories-two-line-location">${memoriesLocationTwoLines(x.city)}</span></span><span class="rest-visit-date"'
hot_new='<span class="meta hotel-location memories-two-line-location">${memoriesLocationTwoLines(x.city)}</span><span class="hotel-visit-date">'
s=s.replace(res_old,res_new,1)
s=s.replace(hot_old,hot_new,1)
css='''<style id="memories-v2-city-country-lines">
#listScreen #list .cardInfo .memories-two-line-location,
#hotelScreen #hotelList .cardInfo .memories-two-line-location {
display:flex!important;flex-direction:column!important;align-items:flex-start!important;
width:100%!important;max-width:100%!important;min-width:0!important;
overflow:hidden!important;white-space:normal!important;
font-size:clamp(11px,1.5vw,14px)!important;line-height:1.05!important;margin-top:2px!important;
}
#listScreen #list .memories-two-line-location .place-city,
#listScreen #list .memories-two-line-location .place-country,
#hotelScreen #hotelList .memories-two-line-location .place-city,
#hotelScreen #hotelList .memories-two-line-location .place-country {
display:block!important;width:100%!important;max-width:100%!important;
overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;
line-height:1.05!important;min-height:1.05em!important;
}
@media (max-width:580px){
#listScreen #list .cardInfo .memories-two-line-location,
#hotelScreen #hotelList .cardInfo .memories-two-line-location{font-size:11px!important}
}
</style>'''
assert '</head>' in s
s=s.replace('</head>',css+'</head>',1)
html_path.write_text(s,encoding="utf-8")
print("Offline globe coordinate inference and live counter refresh prepared.")

# Icon: derive it from the existing approved Memories leather-bound cover image.
m=re.search(r'id="memoriesCover"[\s\S]{0,1400}?<img[^>]+src="data:image/png;base64,([A-Za-z0-9+/=]+)"',s)
if not m:
    raise RuntimeError("Approved cover image not found - refusing a generic replacement icon")
from PIL import Image, ImageOps
cover=Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGB")
w,h=cover.size
# Square crop shows Memories lettering and the blue globe.
box=(int(w*.08),int(h*.075),int(w*.92),int(h*.075)+int(w*.84))
icon=cover.crop(box)
icon=ImageOps.fit(icon,(512,512),method=Image.Resampling.LANCZOS)
out=Path("app/src/main/res/drawable-nodpi/memories_launcher.png")
out.parent.mkdir(parents=True,exist_ok=True)
icon.save(out,optimize=True)
manifest=Path("app/src/main/AndroidManifest.xml")
xml=manifest.read_text()
assert 'android:icon=' not in xml
xml=xml.replace('<application','<application android:icon="@drawable/memories_launcher"',1)
manifest.write_text(xml)
print("Custom icon generated from the validated cover:",out)


# Memories V2 book flow: restaurants -> hotels -> globe -> silent back cover.
# The source book navigation is patched after the workflow's 'globe' -> 'map'
# compatibility fix, avoiding changes to any saved experiences or photo fields.
pages_before="const pages=['map','list','hotels'];"
pages_after="const pages=['list','hotels','map','end'];"
assert s.count(pages_before)==1, "Expected exactly one V2 page sequence"
s=s.replace(pages_before,pages_after,1)

# Distinguish the same establishment from another only by its city, not
# by whether the country is written Suisse or Switzerland.
group_before="const key=p.kind+'|'+norm(p.name)+'|'+norm(p.city);"
group_after="const cityCore=memoriesCityKey(p.city);const key=p.kind+'|'+norm(p.name)+'|'+cityCore;"
assert s.count(group_before)==1,"Unexpected map-grouping code"
s=s.replace(group_before,group_after,1)

# Hotel photo enlargement: preserve the approved star plaques, place/date and card heights.
hotel_photo_css = r'''<style id="memories-v2-hotel-photo-enlargement">
#hotelScreen #hotelList .rowBtn{
  grid-template-columns:clamp(142px,28vw,195px) minmax(0,1fr) auto!important;
}
#hotelScreen #hotelList .visual{
  width:100%!important;max-width:none!important;
  height:100%!important;min-height:126px!important;
  overflow:hidden!important;
}
#hotelScreen #hotelList .visual img{
  width:100%!important;height:100%!important;object-fit:cover!important;
}
#hotelScreen #hotelList .cardInfo{
  min-width:0!important;
}
@media(max-width:500px){
  #hotelScreen #hotelList .rowBtn{
    grid-template-columns:clamp(118px,30vw,155px) minmax(0,1fr) auto!important;
  }
}
</style>'''
assert s.count('</head>')==1
s=s.replace('</head>',hotel_photo_css+'</head>',1)

# A dedicated blank end cover, still part of the book (not the home cover).
# It uses the same approved burgundy/gold leather color palette.
end_page=r'''
<style id="memories-v2-end-page-style">
#endScreen{display:none!important;min-height:100dvh;padding:0!important;background:#210714!important}
#endScreen.active{display:flex!important;align-items:center;justify-content:center}
#memoriesEndBook{position:relative;display:block;width:min(100vw,65vh);height:min(100dvh,155vw);max-width:100%;max-height:100dvh;min-height:86dvh;background:
radial-gradient(ellipse at 42% 38%,#8c191f 0%,#65080f 49%,#340307 100%);border:16px ridge #6b080d;border-radius:25px 19px 17px 25px;
box-shadow:inset 0 0 0 5px #250105,inset 0 0 22px #170105,8px 3px 22px #000b}
#memoriesEndBook::before{content:'';position:absolute;inset:16px 18px 25px 15px;border:5px double #e8ac38;box-shadow:0 0 0 2px #502206,inset 0 0 0 3px #3b060a,inset 0 0 16px #120002;pointer-events:none}
#memoriesEndBook::after{content:'';position:absolute;left:10px;right:10px;bottom:1px;height:13px;
background:linear-gradient(180deg,#ffe082,#dca42f 32%,#fff1a0 53%,#92500c 100%);border-radius:0 0 12px 12px;box-shadow:0 0 4px #1b0205}
#memoriesEndBook .book-corner{position:absolute;z-index:1;color:#e9aa34;font-family:serif;font-size:clamp(43px,11vw,85px);line-height:1;text-shadow:1px 2px 0 #76360b,0 0 7px #ffde8b}
#memoriesEndBook .tl{top:20px;left:21px}#memoriesEndBook .tr{top:20px;right:21px;transform:scaleX(-1)}
#memoriesEndBook .bl{bottom:36px;left:21px;transform:scaleY(-1)}
#memoriesEndBook .br{bottom:36px;right:21px;transform:scale(-1)}
#memBookTools{top:calc(env(safe-area-inset-top,0px) + 18px)!important;right:18px!important;
width:43px!important;height:43px!important;padding:0!important;display:grid!important;place-items:center!important;
border:1.5px solid #d9ad60!important;border-radius:50%!important;
background:radial-gradient(circle at 32% 22%,#7e3655,#351022 72%)!important;
color:#ffe4aa!important;font:22px Georgia,serif!important;box-shadow:inset 0 0 0 2px #371423,0 4px 14px #0008!important}
#memBookTools[hidden]{display:none!important}
#memBookMenu{top:calc(env(safe-area-inset-top,0px) + 66px)!important}
</style>
<section id="endScreen" class="screen" aria-label="Blank back cover">
 <div id="memoriesEndBook" aria-hidden="true"><span class="book-corner tl">❦</span><span class="book-corner tr">❦</span><span class="book-corner bl">❦</span><span class="book-corner br">❦</span></div>
</section>
'''
anchor='<style id="memoriesBookNavigationStyles">'
assert s.count(anchor)==1
s=s.replace(anchor,end_page+anchor,1)
button_before='<button id="memBookTools" type="button" hidden aria-label="Open tools">☰ Tools</button>'
assert s.count(button_before)==1
s=s.replace(button_before,'<button id="memBookTools" type="button" hidden aria-label="Tools" title="Tools">✦</button>',1)

# Keep navigation working for the new final page; it is deliberately blank.
tab_before="const result=oldShowTab.apply(this,arguments);"
tab_after="""if(page==='end'){
        document.querySelectorAll('.screen').forEach(el=>el.classList.remove('active'));
        document.getElementById('endScreen').classList.add('active');
        sync();window.scrollTo(0,0);return;
      }
      document.getElementById('endScreen').classList.remove('active');
      const result=oldShowTab.apply(this,arguments);"""
assert s.count(tab_before)==1
s=s.replace(tab_before,tab_after,1)
sync_before="tools.hidden=covered;hint.hidden=covered;arrows.hidden=covered;"
sync_after="tools.hidden=covered||current==='end';hint.hidden=covered||current==='end';arrows.hidden=covered||current==='end';"
assert s.count(sync_before)==1
s=s.replace(sync_before,sync_after,1)
touch_before="#mapScreen,#listScreen,#hotelScreen'))return;"
touch_after="#globeScreen,#listScreen,#hotelScreen,#mapScreen,#endScreen'))return;"
assert s.count(touch_before)==1
s=s.replace(touch_before,touch_after,1)
observer_before="const observer=new MutationObserver(sync);"
observer_after="cover.addEventListener('click',function(){window.showTab('list');window.scrollTo(0,0)});\n  const observer=new MutationObserver(sync);"
assert s.count(observer_before)==1
s=s.replace(observer_before,observer_after,1)

html_path.write_text(s,encoding='utf-8')
print("Book flow + blank end page + compact tools button + country-proof grouping ready.")
