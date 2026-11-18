"""Add touch crop editor for restaurant and hotel card photos."""
from pathlib import Path
p=Path("app/src/main/assets/index.html")
s=p.read_text(encoding="utf-8")
old="async function imageToDataURL(file){return new Promise((resolve,reject)=>{let fr=new FileReader();fr.onerror=reject;fr.onload=()=>{let im=new Image();im.onerror=reject;im.onload=()=>{let max=850,scale=Math.min(1,max/Math.max(im.width,im.height)),c=document.createElement('canvas');c.width=Math.round(im.width*scale);c.height=Math.round(im.height*scale);c.getContext('2d').drawImage(im,0,0,c.width,c.height);resolve(c.toDataURL('image/jpeg',.65))};im.src=fr.result};fr.readAsDataURL(file)})}"
assert s.count(old)==1, "Photo converter changed unexpectedly"
new=r"""async function imageToDataURL(file){
  const url=URL.createObjectURL(file);
  try {
    const img=await new Promise((resolve,reject)=>{
      const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('Cannot open photo'));image.src=url;
    });
    return await memoriesCropPhoto(img);
  } finally {URL.revokeObjectURL(url)}
}
function memoriesCropPhoto(img){
 return new Promise((resolve,reject)=>{
  const modal=document.createElement('div');modal.id='memoriesCropEditor';
  modal.innerHTML='<div class="mem-crop-panel"><div class="mem-crop-title">Adjust photo</div><div class="mem-crop-help">Move with one finger · Pinch with two fingers to zoom</div><canvas id="memCropCanvas" width="540" height="360"></canvas><div class="mem-crop-controls"><label>Zoom <input id="memCropZoom" type="range" min="1" max="4" step=".01" value="1"></label><button type="button" id="memCropCancel">Cancel</button><button type="button" id="memCropSave">Use photo</button></div></div>';
  document.body.appendChild(modal);
  const canvas=modal.querySelector('canvas'),ctx=canvas.getContext('2d');
  const slider=modal.querySelector('#memCropZoom');
  const pointers=new Map();let zoom=1,dx=0,dy=0,gesture=null,done=false;
  const base=Math.max(canvas.width/img.width,canvas.height/img.height);
  const draw=()=>{
   const scale=base*zoom,w=img.width*scale,h=img.height*scale;
   const limitX=Math.max(0,(w-canvas.width)/2),limitY=Math.max(0,(h-canvas.height)/2);
   dx=Math.max(-limitX,Math.min(limitX,dx));dy=Math.max(-limitY,Math.min(limitY,dy));
   ctx.clearRect(0,0,canvas.width,canvas.height);
   ctx.drawImage(img,(canvas.width-w)/2+dx,(canvas.height-h)/2+dy,w,h);
   slider.value=String(zoom);
  };
  const finish=(result,error)=>{
   if(done)return;done=true;modal.remove();
   if(error)reject(error);else resolve(result);
  };
  slider.oninput=()=>{zoom=Number(slider.value);draw()};
  const state=()=>[...pointers.values()];
  canvas.onpointerdown=e=>{e.preventDefault();canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});gesture=null};
  canvas.onpointermove=e=>{
   if(!pointers.has(e.pointerId))return;e.preventDefault();
   const prev=state(),before=pointers.get(e.pointerId);
   pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
   const now=state();
   if(now.length===1){dx+=e.clientX-before.x;dy+=e.clientY-before.y}
   else if(now.length===2){
    const dist=a=>Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y);
    const oldDist=dist(prev),newDist=dist(now);
    if(oldDist>0)zoom=Math.max(1,Math.min(4,zoom*newDist/oldDist));
    dx+=((now[0].x+now[1].x)-(prev[0].x+prev[1].x))/2;
    dy+=((now[0].y+now[1].y)-(prev[0].y+prev[1].y))/2;
   }
   draw();
  };
  const release=e=>{pointers.delete(e.pointerId)};
  canvas.onpointerup=release;canvas.onpointercancel=release;
  canvas.onwheel=e=>{e.preventDefault();zoom=Math.max(1,Math.min(4,zoom*(e.deltaY<0?1.1:.9)));draw()};
  modal.querySelector('#memCropCancel').onclick=()=>finish(null,new Error('Photo selection cancelled'));
  modal.querySelector('#memCropSave').onclick=()=>{
   const output=document.createElement('canvas');output.width=810;output.height=540;
   output.getContext('2d').drawImage(canvas,0,0,810,540);
   finish(output.toDataURL('image/jpeg',.82));
  };
  draw();
 });
}"""
s=s.replace(old,new,1)
s=s.replace("</head>","""<style id="memories-photo-crop-style">
#memoriesCropEditor{position:fixed;inset:0;z-index:2147483647;background:#180812ef;display:flex;align-items:center;justify-content:center;padding:12px}
.mem-crop-panel{background:#4b1830;color:#ffe9ba;border:2px solid #c69b56;border-radius:14px;padding:14px;max-width:min(96vw,720px);width:100%;box-shadow:0 15px 45px #000a}
.mem-crop-title{font-size:22px;font-weight:700;text-align:center}
.mem-crop-help{text-align:center;font-size:13px;margin:8px 0}
#memCropCanvas{display:block;width:100%;height:auto;max-height:60dvh;object-fit:contain;touch-action:none;background:#180812;border:1px solid #c69b56}
.mem-crop-controls{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-top:12px}
.mem-crop-controls label{display:flex;gap:6px;align-items:center}
.mem-crop-controls button{background:#b28a53;color:#210c16;border:0;border-radius:8px;padding:12px 16px;font-weight:bold}
</style></head>""",1)
assert 'function memoriesCropPhoto(img)' in s
assert s.count('async function imageToDataURL(file)')==1
p.write_text(s,encoding='utf-8')
print('Restaurant and hotel card photo crop editor installed')
