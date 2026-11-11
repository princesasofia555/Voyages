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
