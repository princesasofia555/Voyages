"""Add the newly reported 16 November 2026 visit without removing the earlier visit."""
from pathlib import Path
import json,re
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
m=re.search(r"const BASE=(\[.*?\]);",s,re.S)
assert m,"Restaurant list not found"
base=json.loads(m.group(1))
new={"name":"La Cuisine de Neusa","date":"16.11.2026","city":"Etoy Switzerland","address":"Route Suisse 24, 1163 Etoy, Switzerland","year":"2026","mich":"","gault":"—","notes":"","lat":46.4867,"lon":6.4196,"i":51,"_uid":"memories_v4_neusa_20261116"}
if not any(x.get("name","").casefold()==new["name"].casefold() and x.get("date")==new["date"] for x in base):
    base.append(new)
s=s[:m.start(1)]+json.dumps(base,ensure_ascii=False,separators=(",",":"))+s[m.end(1):]
p.write_text(s,encoding="utf-8")
print("Visit of 16.11.2026 included separately from 09.10.2026.")
