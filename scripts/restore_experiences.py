"""Restore the six missing experiences without overwriting user data."""
from pathlib import Path
import json
import re
p = Path("app/src/main/assets/index.html")
s = p.read_text(encoding="utf-8")
missing = json.loads("[{\"name\":\"Le Berceau des Sens\",\"date\":\"11.11.2026\",\"city\":\"Lausanne Switzerland\",\"address\":\"Route de Berne 301 1000 Lausanne\",\"year\":\"2026\",\"mich\":\"★\",\"gault\":\"16\",\"notes\":\"\",\"lat\":46.507,\"lon\":6.6302,\"i\":45,\"_uid\":\"u1794410316488\"},{\"name\":\"Casino de Morges\",\"date\":\"07.11.2026\",\"city\":\"Morges switzerland\",\"address\":\"Place du Casino 4 1110 Morges\",\"year\":\"2026\",\"mich\":\"\",\"gault\":\"15\",\"notes\":\"Pithiviers pigeau au top\",\"lat\":46.5062,\"lon\":6.4948,\"i\":46,\"_uid\":\"u1794413297337\"},{\"name\":\"Le Riviera\",\"date\":\"06.11.2026\",\"city\":\"Montreux Switzerland\",\"address\":\"Rue du thêàtre 9, 1820 Montreux\",\"year\":\"2026\",\"mich\":\"\",\"gault\":\"—\",\"notes\":\"Gatsby night avec Mushta, Lurdes et JC\",\"lat\":46.426,\"lon\":6.918,\"i\":47,\"_uid\":\"u1794413491582\"},{\"name\":\"La Poesia\",\"date\":\"06.11.2026\",\"city\":\"Lausanne Switzerland\",\"address\":\"Av. du Chablais 53, 1007 Lausanne\",\"year\":\"2026\",\"mich\":\"\",\"gault\":\"14\",\"notes\":\"Avec team Hydromea\",\"lat\":46.5235,\"lon\":6.6017,\"i\":48,\"_uid\":\"u1794413683479\"},{\"name\":\"Café de Peney\",\"date\":\"11.12.2025\",\"city\":\"Satigny Switzerland\",\"address\":\"Rte d'Aire-la-Ville 130, 1242 Satigny\",\"year\":\"2025\",\"mich\":\"\",\"gault\":\"14\",\"notes\":\"La bonne nouvelle arrive🩷. Je serai encore marraine\",\"lat\":46.1989,\"lon\":6.0318,\"i\":49,\"_uid\":\"u1794413930695\"},{\"name\":\"Café de Peney\",\"date\":\"17.05.2025\",\"city\":\"Satigny Switzerland\",\"address\":\"Rte d'Aire-la-Ville 130, 1242 Satigny\",\"year\":\"2025\",\"mich\":\"\",\"gault\":\"14\",\"notes\":\"Avec la famille Robin🥰. Lili confortable dans le ventre de maman🩷\",\"lat\":46.1989,\"lon\":6.0318,\"i\":50,\"_uid\":\"u1794414022663\"}]")
match = re.search(r"const BASE=(\[.*?\]);", s, re.S)
if not match:
    raise SystemExit("Restaurant BASE not found")
base = json.loads(match.group(1))
seen = {(r.get("name"), r.get("date")) for r in base}
for row in missing:
    if (row["name"], row["date"]) not in seen:
        base.append(row)
s = s[:match.start(1)] + json.dumps(base, ensure_ascii=False, separators=(",", ":")) + s[match.end(1):]
# Existing app installations store the earlier 44-item list. Merge only the six missing
# entries at startup; do not overwrite edits, photos, or other stored experiences.
needle = "RECENT_RESTAURANT_PHOTOS[44]="
if needle not in s:
    raise SystemExit("Expected restaurant initialization marker not found")
migration = """;for(const memory of BASE){if(memory._uid&&!items.some(r=>r._uid===memory._uid||(r.name===memory.name&&r.date===memory.date))){items.push(memory)}}try{localStorage.setItem(KEY,JSON.stringify(items))}catch(e){};"""
s = s.replace(needle, migration + needle, 1)
p.write_text(s, encoding="utf-8")
print("Restored six missing restaurant visits; preserved stored memories.")
