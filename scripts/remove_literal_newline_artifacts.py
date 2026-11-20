#!/usr/bin/env python3
"""Remove literal escaped newline text nodes without changing app content or CSS."""
from pathlib import Path
from html.parser import HTMLParser
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.raw=[]
        self.stack=[]
    def handle_starttag(self,tag,attrs):
        self.stack.append(tag)
    def handle_endtag(self,tag):
        if tag in self.stack:
            self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
    def handle_data(self,data):
        if "script" not in self.stack and "style" not in self.stack and data.strip()==r"\n\n":
            self.raw.append((self.getpos(),data))
parser=Parser()
parser.feed(s)
# Only remove exact isolated text outside tags. Preserve JavaScript, CSS and
# legitimate restaurant/hotel descriptions, including newlines inside strings.
if parser.raw:
    lines=s.splitlines(keepends=True)
    for (line,col),data in reversed(parser.raw):
        start=sum(map(len,lines[:line-1]))+col
        assert s[start:start+len(data)]==data
        s=s[:start]+s[start+len(data):]
    p.write_text(s,encoding="utf-8")
print("Removed",len(parser.raw),"isolated escaped-newline text nodes")
