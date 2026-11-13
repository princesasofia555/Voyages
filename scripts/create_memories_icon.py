"""Create the Android launcher icon from the validated Memories book cover."""
from pathlib import Path
import base64
import re
from io import BytesIO
from PIL import Image

html = Path("app/src/main/assets/index.html").read_text(encoding="utf-8")
match = re.search(r'id="memoriesCover".*?<img[^>]+src="data:image/png;base64,([^"]+)', html, re.S)
if not match:
    raise SystemExit("Validated Memories cover not found: refusing to use another image")
cover = Image.open(BytesIO(base64.b64decode(match.group(1)))).convert("RGBA")
canvas = Image.new("RGBA", (512, 512), (38, 12, 24, 255))
# Fit the entire approved portrait cover, without cropping or redesigning it.
cover.thumbnail((504, 504), Image.Resampling.LANCZOS)
canvas.alpha_composite(cover, ((512-cover.width)//2, (512-cover.height)//2))
dest = Path("app/src/main/res/drawable-nodpi/memories_launcher.png")
dest.parent.mkdir(parents=True, exist_ok=True)
canvas.save(dest, optimize=True)
print("Generated icon from validated book cover:", dest)
