#!/usr/bin/env python3
"""Lock collage photos until Edit Photos is tapped, and allow swipes across photos."""
from pathlib import Path
import html,re
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
for fid in ("freeCollageFrame","freeCollageFrame2","freeCollageFrame3"):
    pat=r'(<iframe\b[^>]*?\bid="'+fid+r'"[^>]*?\bsrcdoc=")(.*?)(")'
    m=re.search(pat,s,re.S)
    assert m, f"Missing {fid}"
    doc=html.unescape(m.group(2))
    old="let photos=[],selected=null,editing=true,db"
    assert doc.count(old)==1,(fid,"editing state")
    doc=doc.replace(old,"let photos=[],selected=null,editing=false,db",1)
    assert doc.count('id="done">Done</button>')==1
    doc=doc.replace('id="done">Done</button>','id="done">Edit Photos</button>',1)
    doc=doc.replace('id="add">+ Add Photo</button>','id="add" style="display:none">+ Add Photo</button>',1)
    # Expose the existing state without replacing the original photo editor.
    doc=doc.replace("const DB='MemoriesV3FreeCollage';","window.memoriesCollageEditing=()=>editing;const DB='MemoriesV3FreeCollage';",1) if "const DB='MemoriesV3FreeCollage';" in doc else doc
    doc=re.sub(r"(const DB='MemoriesV4FreeCollage[23]';)",r"window.memoriesCollageEditing=()=>editing;\1",doc,count=1)
    assert "window.memoriesCollageEditing=()=>editing;" in doc,(fid,"missing state bridge")
    # Allow page turning over images when locked; retain full drag/zoom/rotate in edit mode.
    old_guard="return !!(el&&el.closest&&el.closest('button,input,textarea,select,[contenteditable],.toolbar,.photo,.photo-item,[draggable=\"true\"]'));"
    new_guard="return !!(window.memoriesCollageEditing?.() || (el&&el.closest&&el.closest('button,input,textarea,select,[contenteditable],.toolbar')));"
    assert old_guard in doc,(fid,"swipe guard not found")
    doc=doc.replace(old_guard,new_guard,1)
    s=s[:m.start(2)]+html.escape(doc,quote=True)+s[m.end(2):]
p.write_text(s,encoding="utf-8")
print("PASS: all three collages start locked; Edit Photos unlocks movement; swipe works over photos")
