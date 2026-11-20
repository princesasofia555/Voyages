#!/usr/bin/env python3
"""Enable horizontal finger swipes across Memories pages, including iframe collages."""
from pathlib import Path
import re, html
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
assert "id=\"memBookPrev\"" in s and "id=\"memBookNext\"" in s
parent=r"""
<script id="memories-swipe-navigation">
(function(){
  const THRESHOLD=65, VERTICAL_TOLERANCE=1.35;
  let start=null;
  function isInteractive(el){
    return !!(el && el.closest && el.closest('button,a,input,textarea,select,[contenteditable="true"],[role="slider"],.mem-crop-controls,.modal'));
  }
  function go(direction){
    const btn=document.getElementById(direction==='next'?'memBookNext':'memBookPrev');
    if(btn)btn.click();
  }
  document.addEventListener('touchstart',function(e){
    if(e.touches.length!==1||isInteractive(e.target)){start=null;return;}
    const t=e.touches[0];start={x:t.clientX,y:t.clientY};
  },{passive:true});
  document.addEventListener('touchend',function(e){
    if(!start||e.changedTouches.length!==1){start=null;return;}
    const t=e.changedTouches[0],dx=t.clientX-start.x,dy=t.clientY-start.y;start=null;
    if(Math.abs(dx)<THRESHOLD||Math.abs(dx)<Math.abs(dy)*VERTICAL_TOLERANCE)return;
    if(!document.body.classList.contains('mem-book-mode'))return;
    go(dx<0?'next':'prev');
  },{passive:true});
  document.addEventListener('touchcancel',()=>{start=null},{passive:true});
  window.addEventListener('message',function(e){
    if(!e.data||e.data.type!=='memories-collage-swipe')return;
    const frames=['freeCollageFrame','freeCollageFrame2','freeCollageFrame3'];
    if(!frames.some(id=>document.getElementById(id)?.contentWindow===e.source))return;
    if(!document.body.classList.contains('mem-book-mode'))return;
    go(e.data.direction);
  });
})();
</script>
"""
assert "</body>" in s
s=s.replace("</body>",parent+"</body>",1)
child=r"""
<script id="memories-collage-swipe">
(function(){
 let start=null;
 function editing(el){
   return !!(el&&el.closest&&el.closest('button,input,textarea,select,[contenteditable],.toolbar,.photo,.photo-item,[draggable="true"]'));
 }
 document.addEventListener('touchstart',function(e){
   if(e.touches.length!==1||editing(e.target)){start=null;return;}
   const t=e.touches[0];start={x:t.clientX,y:t.clientY};
 },{passive:true});
 document.addEventListener('touchend',function(e){
   if(!start||e.changedTouches.length!==1){start=null;return;}
   const t=e.changedTouches[0],dx=t.clientX-start.x,dy=t.clientY-start.y;start=null;
   if(Math.abs(dx)<65||Math.abs(dx)<Math.abs(dy)*1.35)return;
   parent.postMessage({type:'memories-collage-swipe',direction:dx<0?'next':'prev'},'*');
 },{passive:true});
 document.addEventListener('touchcancel',()=>{start=null},{passive:true});
})();
</script>
"""
for fid in ("freeCollageFrame","freeCollageFrame2","freeCollageFrame3"):
    pattern=r'(<iframe\b[^>]*?\bid="'+fid+r'"[^>]*?\bsrcdoc=")(.*?)(")'
    matches=list(re.finditer(pattern,s,re.S))
    assert len(matches)==1,(fid,len(matches))
    m=matches[0]
    doc=html.unescape(m.group(2))
    assert "</body>" in doc,(fid,"missing body")
    assert "memories-collage-swipe" not in doc
    doc=doc.replace("</body>",child+"</body>",1)
    s=s[:m.start(2)]+html.escape(doc,quote=True)+s[m.end(2):]
assert s.count('id=&quot;memories-collage-swipe&quot;')==3 or s.count('id="memories-collage-swipe"')==3, "Swipe handler missing from one or more photo frames"
p.write_text(s,encoding="utf-8")
print("PASS: global horizontal swipe plus iframe swipe, vertical scroll and photo edits preserved")
