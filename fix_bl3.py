f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

# Fix button style
old2="  if(btn)btn.textContent=isBlocked?'\U0001f513 Убрать из ЧС':'\U0001f512 Добавить в ЧС';"
new2="  if(btn){btn.textContent=isBlocked?'\U0001f513 Убрать из ЧС':'\U0001f512 Добавить в ЧС';btn.className=isBlocked?'ctx-item':'ctx-item danger';}"
print('btn:', old2 in c)
if old2 in c: c=c.replace(old2,new2)

# Fix setTimeout - add inpArea show before updateBlockedBar
old3="  // Update input area based on blacklist\n  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); else { const inpArea=document.getElementById('inpArea');if(inpArea)inpArea.style.display='flex';const bar=document.getElementById('blockedBar');if(bar)bar.style.display='none'; }},50);"
new3="  const _ia=document.getElementById('inpArea');if(_ia)_ia.style.display='flex';\n  const _bb=document.getElementById('blockedBar');if(_bb)_bb.style.display='none';\n  setTimeout(()=>{if(type==='peer')updateBlockedBar(id);},10);"
print('timeout:', old3 in c)
if old3 in c: c=c.replace(old3,new3)

open('ui/gui.py','w',encoding='utf-8').write(c)
print('Done!')
