"""Put original gold ornaments, rose, bell and pen above movable collage photos."""
from pathlib import Path
from PIL import Image
from io import BytesIO
import base64, html, re

p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
start=s.index('<section id="collageScreen"')
end=s.index('</section>',start)
part=html.unescape(s[start:end])
m=re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)',part)
assert m, 'Original approved collage artwork not found'
raw=base64.b64decode(m.group(1))
im=Image.open(BytesIO(raw)).convert('RGBA')
w,h=im.size
# Geometry-only foreground regions: never classify individual red/gold pixels.
# This preserves the original rose petals, bell and pen without scattered dots.
from PIL import ImageDraw
mask=Image.new('L',(w,h),0)
d=ImageDraw.Draw(mask)
# Slim original frame around the whole page.
edge=max(8,round(w*.025))
d.rectangle((0,0,w,edge),fill=255)
d.rectangle((0,h-edge,w,h),fill=255)
d.rectangle((0,0,edge,h),fill=255)
d.rectangle((w-edge,0,w,h),fill=255)
# Top-left gold ornament only; no diagonal artwork across photographs.
d.polygon([(0,0),(.53*w,0),(.53*w,.10*h),(.30*w,.10*h),(.20*w,.16*h),(.13*w,.25*h),(0,.25*h)],fill=255)
# Bottom still-life stays complete, including the rose's pale interior.
d.polygon([(0,.78*h),(.37*w,.78*h),(.48*w,.72*h),(.55*w,.67*h),(.76*w,.64*h),(.93*w,.67*h),(w,.62*h),(w,h),(0,h)],fill=255)
# A single intact foreground illustration, never a pixel-by-pixel color cutout.
im.putalpha(mask)
buf=BytesIO();im.save(buf,format='PNG',optimize=True)
overlay='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
# Remove former horizontal opaque background strips.
old="""#page::before,#page::after{
 content:'';position:absolute;pointer-events:none;z-index:9000;
 background-image:inherit;background-repeat:no-repeat;
 background-size:100vw 100dvh;
}
#page::before{left:0;top:0;width:100%;height:18%;background-position:left top}
#page::after{left:0;bottom:0;width:100%;height:24%;background-position:left bottom}"""
# Replace the known CSS markers using string boundaries rather than regex:
# HTML escaping inside srcdoc differs from normal CSS.
marker='#page::before,#page::after'
ending='height:24%;background-position:left bottom}'
assert s.count(marker)==3, f'Expected 3 collage overlays, got {s.count(marker)}'
assert s.count(ending)>=2, f'Expected collage endings, got {s.count(ending)}'
new="#page::before{content:'';position:absolute;inset:0;pointer-events:none;z-index:9000;background:url("+overlay+") center/100% 100% no-repeat}#page::after{content:none}"
count=s.count(marker)
for _ in range(count):
    a=s.index(marker)
    b=s.index(ending,a)+len(ending)
    s=s[:a]+new+s[b:]
assert s.count('z-index:9000;background:url(')==count
p.write_text(s,encoding='utf-8')
print('Three original foreground layers applied',w,h)
