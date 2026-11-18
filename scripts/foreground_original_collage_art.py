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
pix=im.load()
mask=Image.new('L',(w,h),0); out=mask.load()
for y in range(h):
 for x in range(w):
  r,g,b,_=pix[x,y]
  # Preserve the actual original pixels, not newly drawn substitutes.
  border=(x<42 or x>w-43 or y<58 or y>h-49)
  top=(y<h*.25 and x<w*.54 and r>105 and g>r*.35 and g>40)
  bottom=y>h*.60 and (
    (r>125 and (g>35 or b>40)) or
    (g>48 and g>r*.44) or
    (r>140 and g>r*.24) or
    (r<43 and g<38 and b<38 and y>h*.70 and x<w*.47)
  )
  if border or top or bottom:out[x,y]=255
# Connect thin gold details and remove jagged holes, without repainting artwork.
mask=mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(1.2))
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
assert s.count(old)==3
new="#page::before{content:'';position:absolute;inset:0;pointer-events:none;z-index:9000;background:url('"+overlay+"') center/100% 100% no-repeat}#page::after{content:none}"
s=s.replace(old,new)
assert s.count('z-index:9000;background:url(')==3
p.write_text(s,encoding='utf-8')
print('Original ornament overlay preserved for all three collage pages',w,h)
