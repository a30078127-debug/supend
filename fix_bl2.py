f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

# Fix 1: remove force show inpArea on line 2649
old1="  document.getElementById('chatHead').style.display='flex';\n  document.getElementById('emptyState').style.display='none';\n  document.getElementById('msgs').style.display='flex';\n  document.getElementById('inpArea').style.display='flex';"
new1="  document.getElementById('chatHead').style.display='flex';\n  document.getElementById('emptyState').style.display='none';\n  document.getElementById('msgs').style.display='flex';"
print('fix1:', old1 in c)
if old1 in c: c=c.replace(old1,new1)

# Fix 2: button style in showPeerCtx
old2="  if(btn)btn.textContent=isBlocked?'🔓 Убрать из ЧС':'🔒 Добавить в ЧС';"
new2="  if(btn){btn.textContent=isBlocked?'🔓 Убрать из ЧС':'🔒 Добавить в ЧС';btn.className=isBlocked?'ctx-item':'ctx-item danger';}"
print('fix2:', old2 in c)
if old2 in c: c=c.replace(old2,new2)

# Fix 3: show inpArea before updateBlockedBar in openChat
old3="  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); else { const inpArea=document.getElementById('inpArea');if(inpArea)inpArea.style.display='flex';const bar=document.getElementById('blockedBar');if(bar)bar.style.display='none'; }},50);"
new3="  const _ia=document.getElementById('inpArea');if(_ia)_ia.style.display='flex';\n  const _bb=document.getElementById('blockedBar');if(_bb)_bb.style.display='none';\n  setTimeout(()=>{ if(type==='peer') updateBlockedBar(id); },10);"
print('fix3:', old3 in c)
if old3 in c: c=c.replace(old3,new3)

open('ui/gui.py','w',encoding='utf-8').write(c)
print('Done!')
