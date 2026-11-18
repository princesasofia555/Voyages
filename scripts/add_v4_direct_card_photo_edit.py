"""Enable direct photo tap on restaurant and hotel list cards."""
from pathlib import Path
p=Path('app/src/main/assets/index.html')
s=p.read_text(encoding='utf-8')
assert 'function memoriesCropPhoto(img)' in s
assert 'function renderHotels(){' in s and 'function render(){' in s
addon=r"""
<script id="memories-card-photo-direct-edit">
(function(){
 async function adjustPhoto(src){
   const img=await new Promise((resolve,reject)=>{
     const image=new Image();
     image.onload=()=>resolve(image);
     image.onerror=()=>reject(new Error('Unable to load the saved photo'));
     image.src=src;
   });
   return await memoriesCropPhoto(img);
 }
 document.addEventListener('click',async function(event){
   const img=event.target.closest('#list .rowBtn .visual img,#hotelList .rowBtn .visual img');
   if(!img)return;
   event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();
   if(document.getElementById('memoriesCropEditor'))return;
   const row=img.closest('.row');
   const list=img.closest('#list,#hotelList');
   const isHotel=list&&list.id==='hotelList';
   const rows=[...list.querySelectorAll(':scope > .row')];
   const visibleIndex=rows.indexOf(row);
   if(visibleIndex<0)return;
   const button=row.querySelector('.rowBtn');
   const handler=button?.getAttribute('onclick')||'';
   let target=null;
   if(isHotel){
     const match=handler.match(/toggleHotel\((\d+)\)/);
     if(match)target=HOTELS[Number(match[1])];
   }else{
     const match=handler.match(/toggle\('([^']+)'\)/);
     if(match)target=items.find(x=>String(x._uid)===match[1]);
   }
   if(!target)return;
   try{
     const cropped=await adjustPhoto(img.currentSrc||img.src);
     if(isHotel){
       const key='voyages_hotel_photo_uid_'+encodeURIComponent(target._uid);
       localStorage.setItem(key,cropped);
       target.photo=cropped;
       renderHotels();
     }else{
       const previous=target.photo;
       target.photo=cropped;
       if(!persist()){target.photo=previous;return}
       render();
     }
   }catch(error){
     if(error&&error.message!=='Photo selection cancelled')
       alert('Unable to adjust photo: '+error.message);
   }
 },true);
})();
</script>
<style id="memories-card-photo-direct-edit-style">
#list .rowBtn .visual img,#hotelList .rowBtn .visual img{cursor:zoom-in;touch-action:manipulation}
</style>
"""
assert s.count('</body>')==1
s=s.replace('</body>',addon+'</body>',1)
assert s.count('memories-card-photo-direct-edit')==2
p.write_text(s,encoding='utf-8')
print('Direct photo editing on both list views enabled')
