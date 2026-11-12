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

# Distinguish MICHELIN Selected from Bib Gourmand with no misleading star/flower.
# Both use the existing red MICHELIN plaque position; actual stars stay unchanged.
no_star_before = """${starCount?michelinFlowers(starCount):'<span class="mic-selected-mark">✿</span>'}"""
no_star_after = """${starCount?michelinFlowers(starCount):''}"""
assert s.count(no_star_before)==1, "Expected Michelin non-star symbol"
s=s.replace(no_star_before,no_star_after,1)

# Bib Gourmand: white tongue-out smiling Michelin-man-style face, not a star.
bib_markup = (
  '<span class="mic-selected-mark mic-bibendum-mark" aria-hidden="true">'
  '<svg viewBox="0 0 48 48" width="32" height="32" xmlns="http://www.w3.org/2000/svg">'
  '<g fill="none" stroke="#fff" stroke-width="2.55" stroke-linecap="round" stroke-linejoin="round">'
  '<path d="M15 36 C11 33 9 30 10 25 C10 21 11 18 13 16 C14 12 18 8 21 8 Q22 4 26 6 Q30 7 31 10 C34 12 35 15 35 16 C38 19 39 23 38 27 C38 31 36 34 33 36"/>'
  '<ellipse cx="19" cy="21.5" rx="4.4" ry="6.6"/>'
  '<ellipse cx="29" cy="21.5" rx="4.4" ry="6.6"/>'
  '<path d="M16.7 33.1 Q23.1 40.0 32 32.8"/>'
  '</g>'
  '<g fill="#fff"><ellipse cx="19.5" cy="23.4" rx="2.55" ry="3.55"/><ellipse cx="28.5" cy="23.4" rx="2.55" ry="3.55"/></g>'
  '<path d="M26.9 34.7 Q27.5 29.8 30.0 28.2 Q32.0 27.5 32.3 30 Q32.1 33.5 28.5 35.7Z" fill="#fff"/>'
  '</svg></span>'
)
assert s.count(no_star_after)==1, "Expected one MICHELIN symbol slot"
bib_symbol = """${starCount?michelinFlowers(starCount):/bib\s*gourmand/i.test(mich)?'""" + bib_markup + """':''}"""
s=s.replace(no_star_after,bib_symbol,1)
mic_class_before='class="rest-plaque michelin" aria-label='
mic_class_after='class="rest-plaque michelin ${/bib\s*gourmand/i.test(mich)?"bib-gourmand":""}" aria-label='
assert s.count(mic_class_before)==1
s=s.replace(mic_class_before,mic_class_after,1)
bib_css='''<style id="memories-bib-gourmand-plaque">
.rest-plaque.michelin.bib-gourmand .mic-caption {display:none!important}
.rest-plaque.michelin.bib-gourmand .mic-bibendum-mark{display:flex!important;align-items:center;justify-content:center;line-height:1!important;margin:0 auto!important;max-height:32px!important}.rest-plaque.michelin.bib-gourmand .mic-bibendum-mark svg {display:block!important;width:32px!important;height:32px!important;flex:0 0 32px!important;stroke-linecap:round}
</style>'''
assert s.count('</head>')==1
s=s.replace('</head>',bib_css+'</head>',1)

# Only one MICHELIN wordmark on restaurant plaques: retain the top brand mark.
michelin_footer_css='''<style id="memories-v3-single-michelin-wordmark">
#listScreen #list .rest-plaque.michelin .mic-footer{display:none!important}
</style>'''
assert s.count('</head>')==1
s=s.replace('</head>',michelin_footer_css+'</head>',1)

# La Fleur de Sel, Cossonay, January 2023: approved Bib Gourmand test case.
fleur_pattern=r'("name": "La Fleur de Sel"[\s\S]{0,450}?"mich": ")Sélection(")'
fleur_matches=len(re.findall(fleur_pattern,s))
assert fleur_matches<=1, "Duplicate Fleur de Sel catalogue entries"
if fleur_matches:
    s=re.sub(fleur_pattern,lambda m:m.group(1)+"Bib Gourmand"+m.group(2),s,count=1)
else:
    print("Fleur de Sel handled at runtime using the existing visit date; catalogue format differs.")

# Existing saved V2 catalogues: update only the original visit's award, if still Selected.
fleur_update=r"""
(function(){
 let changed=false;
 for(const visit of items){
   if(visit.name==='La Fleur de Sel' && visit.date==='13.01.2023' &&
      /^(Sélection|Selection|Selected|Sélection Guide MICHELIN)$/i.test(String(visit.mich||'').trim())){
     visit.mich='Bib Gourmand';changed=true;
   }
 }
 if(changed)persist();
})();
"""
assert s.count('function restaurantPlaques(x){')==1
s=s.replace('function restaurantPlaques(x){',fleur_update+'\nfunction restaurantPlaques(x){',1)

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

# Restaurant photo enlargement: preserve lower-edge alignment of MICHELIN/Gault&Millau plaques.
restaurant_photo_css = r'''<style id="memories-v3-restaurant-photo-enlargement">
/* Restaurant-only: the user-approved Le Café Suisse composition. */
#listScreen #list .rowBtn{
  display:block!important;position:relative!important;
  box-sizing:border-box!important;
  height:clamp(180px,28vw,226px)!important;
  min-height:180px!important;
  width:100%!important;padding:0!important;overflow:hidden!important;
}
#listScreen #list .rowBtn .visual{
  display:block!important;position:absolute!important;
  left:0!important;top:0!important;bottom:0!important;
  width:35%!important;max-width:35%!important;height:100%!important;
  min-height:0!important;overflow:hidden!important;
}
#listScreen #list .rowBtn .visual img{
  display:block;width:100%!important;height:100%!important;object-fit:cover!important;
}
#listScreen #list .rowBtn .cardInfo{
  position:absolute!important;left:calc(35% + 12px)!important;
  right:26px!important;top:10px!important;min-width:0!important;
  max-height:calc(100% - 92px)!important;overflow:hidden!important;
  margin:0!important;padding:0!important;text-align:left!important;
}
#listScreen #list .rowBtn .cardInfo .name{
  display:-webkit-box!important;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden!important;line-height:1.05!important;max-width:100%!important;
}
#listScreen #list .rowBtn .chev{
  position:absolute!important;right:8px!important;top:50%!important;
  transform:translateY(-50%)!important;
}
</style>'''
assert s.count('</head>')==1
s=s.replace('</head>',restaurant_photo_css+'</head>',1)

# Identify the exact name-mapping that translates the restaurant's proper name.
for term in ('City Hall','Restaurant de l’Hôtel de Ville','Hôtel de Ville','function enName','const enName','function enPlace'):
    start=s.find(term)
    if start>=0:
        print("RESTAURANT_NAME_DIAGNOSTIC",term,repr(s[max(0,start-180):start+320]))

# Temporary build diagnostics to locate approved card DOM for precise plaque anchoring.
for term in ('function restaurantPlaques(x){','class="rowBtn"','class="rest-plaque','class="rest-visit-date"','Restaurant de l’Hôtel de Ville','Hôtel de Ville','City Hall'):
    start=s.find(term)
    if start>=0: print("CARD_LAYOUT_DIAGNOSTIC",term,repr(s[max(0,start-400):start+1600]))
# Expanded markup diagnostics for approved restaurant badge ordering.
for term in ('function restaurantPlaques(x){','class="rest-visit-date"','function enPlace(v)','function render(){'):
    start=s.find(term)
    if start>=0: print("RESTAURANT_MARKUP_DETAIL",term,repr(s[start:start+4200]))
# Approved restaurant order: Gault&Millau logo next to photo, yellow plaque center, MICHELIN right.
plaque_order_before='return `<span class="rest-plaques">${mic}${yellow}${white}</span>`;'
plaque_order_after='return `<span class="rest-plaques">${white}${yellow}${mic}</span>`;'
assert s.count(plaque_order_before)==1, "Unexpected restaurant plaque order"
s=s.replace(plaque_order_before,plaque_order_after,1)
plaque_css=r'''<style id="memories-v3-fixed-restaurant-plaques">
/* Restaurant-only: fixed three-zone plaques, based on the approved Café Suisse card.
   Keep the approved 35% photograph and the hotel cards unchanged. */
#listScreen #list .rowBtn .rest-visit-date{
  position:absolute!important;left:calc(35% + 12px)!important;
  bottom:8px!important;z-index:3!important;
  margin:0!important;align-self:auto!important;justify-self:auto!important;
  white-space:nowrap!important;
}
#listScreen #list .rowBtn .rest-plaques{
  display:grid!important;position:absolute!important;
  left:calc(35% + 10px)!important;right:33px!important;
  bottom:8px!important;height:106px!important;
  width:auto!important;min-width:0!important;
  margin:0!important;padding:0!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  align-items:end!important;justify-items:center!important;
  align-self:auto!important;overflow:visible!important;
  pointer-events:none!important;
}
#listScreen #list .rowBtn .rest-plaques > .rest-plaque{
  position:relative!important;left:auto!important;right:auto!important;
  top:auto!important;bottom:auto!important;
  margin:0!important;align-self:end!important;
  justify-self:center!important;transform:none!important;
  max-width:100%!important;
}
#listScreen #list .rowBtn .rest-plaques > .empty{visibility:hidden!important}
#listScreen #list .rowBtn .rest-plaques > .score{
  grid-column:1!important;justify-self:start!important;
  margin-bottom:30px!important;transform-origin:bottom left!important;
}
#listScreen #list .rowBtn .rest-plaques > .gault{
  grid-column:2!important;justify-self:center!important;
  margin-bottom:0!important;transform-origin:bottom center!important;
}
#listScreen #list .rowBtn .rest-plaques > .michelin{
  grid-column:3!important;justify-self:end!important;
  margin-bottom:0!important;transform-origin:bottom right!important;
}
@media(max-width:520px){
  #listScreen #list .rowBtn .rest-plaques > .score{
    transform:scale(.78)!important;
  }
  #listScreen #list .rowBtn .rest-plaques > .gault{
    transform:scale(.82)!important;
  }
  #listScreen #list .rowBtn .rest-plaques > .michelin{
    transform:scale(.82)!important;
  }
}
</style>'''
assert s.count('</head>')==1
s=s.replace('</head>',plaque_css+'</head>',1)

# Inspect all original plaque styles to diagnose conflicting selectors.
for match in list(re.finditer(r'[^{}]{0,180}\b(?:rest-plaques|rest-plaque|michelin|gm-authentic-logo|rest-visit-date)[^{}]{0,180}\{[^{}]{0,1000}\}',s,re.I))[:65]:
    print("PLAQUE_CSS_AUDIT:",repr(match.group(0)[:1150]))
# The old restaurant stylesheet has several competing !important positions.
# Pin each restaurant plaque directly in the generated HTML to beat those rules.
fixed_return_before='return `<span class="rest-plaques">${white}${yellow}${mic}</span>`;'
fixed_return_after=r"""const pinned=(html,col,align,extra='')=>html.replace('<span class="rest-plaque', `<span style="position:relative!important;left:auto!important;right:auto!important;top:auto!important;bottom:auto!important;grid-column:${col}!important;justify-self:${align}!important;align-self:end!important;transform:none!important;margin:0!important;${extra}" class="rest-plaque`);
 return `<span class="rest-plaques" style="position:absolute!important;display:grid!important;left:calc(35% + 12px)!important;right:33px!important;top:auto!important;bottom:23px!important;height:106px!important;width:auto!important;max-width:none!important;margin:0!important;padding:0!important;gap:0!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;align-items:end!important;overflow:visible!important;pointer-events:none!important;">${pinned(white,1,'start','margin-bottom:28px!important;')}${pinned(yellow,2,'center','transform:translateX(40px)!important;width:96px!important;height:96px!important;min-width:96px!important;min-height:96px!important;max-width:96px!important;max-height:96px!important;aspect-ratio:1 / 1!important;box-sizing:border-box!important;')}${pinned(mic,3,'end','width:96px!important;height:96px!important;min-width:96px!important;min-height:96px!important;max-width:96px!important;max-height:96px!important;aspect-ratio:1 / 1!important;box-sizing:border-box!important;background:linear-gradient(140deg,#ec3343,#b60924)!important;color:#fff!important;opacity:1!important;mix-blend-mode:normal!important;filter:none!important;')}</span>`;"""
assert s.count(fixed_return_before)==1,"Expected one restaurant plaque return"
s=s.replace(fixed_return_before,fixed_return_after,1)
rest_date_before='class="rest-visit-date" aria-label="Visit date"'
rest_date_after='class="rest-visit-date" style="position:absolute!important;left:calc(35% + 12px)!important;bottom:2px!important;right:auto!important;top:auto!important;margin:0!important;z-index:4!important;" aria-label="Visit date"'
assert s.count(rest_date_before)==1,"Expected one restaurant date"
s=s.replace(rest_date_before,rest_date_after,1)

# The original red MICHELIN plaque must not inherit a transparent/white tint.
# Keep its gold screws and original artwork but make the red enamel opaque.
mic_fix_css=r'''<style id="memories-v3-michelin-red-repair">
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.michelin{width:96px!important;height:96px!important;min-width:96px!important;min-height:96px!important;aspect-ratio:1/1!important;box-sizing:border-box!important;}
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.michelin {
 background:linear-gradient(135deg,#ef3645,#bd0c26)!important;
 color:#fff!important;opacity:1!important;filter:none!important;
 mix-blend-mode:normal!important;
}
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.michelin .mic-circle{
 opacity:.36!important;pointer-events:none!important;
}
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.score{
 margin-bottom:28px!important;
}
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.gault,
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.michelin{
 width:96px!important;height:96px!important;min-width:96px!important;min-height:96px!important;
 max-width:96px!important;max-height:96px!important;aspect-ratio:1/1!important;transform:none!important;
 box-sizing:border-box!important;
}
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.score{
 justify-self:start!important;transform:none!important;transform-origin:bottom left!important;
}
</style>'''
assert s.count('</head>')==1
s=s.replace('</head>',mic_fix_css+'</head>',1)

# Final approved visual mock-up: slightly larger Gault&Millau toque artwork,
# shifted gently to the right; yellow award closer to red award.
# Restaurant-only: no hotel styles or photo proportions changed.
approved_logo_css=r'''<style id="memories-v3-approved-toques-spacing">
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.gault{
 transform:translateX(40px)!important;
}
#listScreen #list .rowBtn .rest-plaques > .rest-plaque.score .gm-authentic-logo{
 width:98px!important;height:84px!important;max-width:none!important;
 object-fit:contain!important;transform:translateX(5px)!important;
 transform-origin:bottom left!important;
}
</style>'''
assert s.count('</head>')==1
s=s.replace('</head>',approved_logo_css+'</head>',1)

# Correct the original Crissier establishment name when older saved data used English.
name_helper=r'''
function memoriesOriginalRestaurantName(x){
 const name=String(x.name||'');
 if(/crissier/i.test(String(x.city||'')) && /(?:\bCity(?: Hall)?\b|Hôtel de Ville|Hotel de Ville)/i.test(name)){
   return 'Restaurant de l’Hôtel de Ville';
 }
 return name;
}
'''
assert s.count('function render(){')==1
s=s.replace('function render(){',name_helper+'\nfunction render(){',1)
name_card='<span class="name">${esc(x.name)}</span>'
assert s.count(name_card)>=1
s=s.replace(name_card,'<span class="name">${esc(memoriesOriginalRestaurantName(x))}</span>',1)

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
# Use the exact user-approved back-cover image, stored as an offline WebP Android asset.
# Unlike the previous CSS imitation, this includes the ornate gold corners,
# rose, spine and gilded page edges from the approved design.
end_cover_image_css=r'''
#endScreen{background:#27020c!important;padding:0!important}
#endScreen.active{display:flex!important;align-items:center!important;justify-content:center!important}
#memoriesEndBook{
 width:min(100vw,62.6dvh)!important;
 height:min(100dvh,159.85vw)!important;
 min-height:0!important;
 max-width:100vw!important;max-height:100dvh!important;
 border:0!important;border-radius:0!important;
 box-shadow:none!important;
 background:#3a0510 url("memories_approved_back_cover.webp") center center / contain no-repeat!important;
}
#memoriesEndBook::before,#memoriesEndBook::after,#memoriesEndBook .book-corner{display:none!important}
'''
end_page=end_page.replace('</style>',end_cover_image_css+'</style>',1)
assert 'memories_approved_back_cover.webp' in end_page

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
