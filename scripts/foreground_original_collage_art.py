"""Put original gold ornaments, rose, bell and pen above movable collage photos."""
from pathlib import Path
from PIL import Image, ImageFilter
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
# Smooth localized overlay regions. Never use pixel-color thresholds or
# angular polygon masks, which produced red speckles and hard white cuts.
from PIL import ImageDraw
mask=Image.new('L',(w,h),0)
d=ImageDraw.Draw(mask)
edge=max(8,round(w*.025))
d.rectangle((0,0,w,edge),fill=255)
d.rectangle((0,h-edge,w,h),fill=255)
d.rectangle((0,0,edge,h),fill=255)
d.rectangle((w-edge,0,w,h),fill=255)
# Soft top-left gold ornament, outside the main photo area.
d.ellipse((-int(.25*w),-int(.18*h),int(.48*w),int(.31*h)),fill=255)
# Soft complete bottom still-life (bell, pen, rose and leaves).
d.rectangle((0,int(.86*h),w,h),fill=255)
d.ellipse((int(.37*w),int(.66*h),int(1.06*w),int(1.02*h)),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(max(4,round(w*.012))))
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
