"""Install seven original restaurant photos, matched by exact name AND date.
Never replace a photo that the user has already set.
"""
from pathlib import Path
import json, re
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
photos=json.loads(Path("scripts/v4_restored_photo_data.json").read_text(encoding="utf-8"))
assert len(photos)==7 and all(x["photo"].startswith("data:image/") for x in photos)
m=re.search(r"const BASE=(\[.*?\]);",s,re.S)
assert m,"BASE restaurant list missing"
base=json.loads(m.group(1))
matched=[]
for entry in photos:
    matches=[r for r in base if r.get("name","").casefold()==entry["name"].casefold() and r.get("date")==entry["date"]]
    assert len(matches)==1,(entry["name"],entry["date"],len(matches))
    row=matches[0]
    if not row.get("photo") or not str(row["photo"]).startswith("data:image/"):
        row["photo"]=entry["photo"]
    matched.append((entry["name"],entry["date"]))
s=s[:m.start(1)]+json.dumps(base,ensure_ascii=False,separators=(",",":"))+s[m.end(1):]
# In a fresh install, the BASE entries are used. In an existing installation,
# only fill missing photos; do not replace the user's edits or existing images.
needle="const KEY='voyages_restaurants_final_v3';let items;"
assert needle in s
s=s.replace(needle, """const KEY='voyages_restaurants_final_v3';let items;""",1)
marker="try{localStorage.setItem(KEY,JSON.stringify(items))}catch(e){};"
assert marker in s
s=s.replace(marker, """for(const restored of BASE){
  const existing=items.find(x=>x.name===restored.name&&x.date===restored.date);
  if(existing&&restored.photo&&(!existing.photo||!String(existing.photo).startsWith('data:image/')))existing.photo=restored.photo;
}
"""+marker,1)
p.write_text(s,encoding="utf-8")
print("Restored",len(matched),"dated original restaurant photos",matched)
