f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

old="""  // Reply preview
  if(m.replyTo){
    const rp=document.createElement('div');rp.className='reply-preview';
    rp.innerHTML=<div class=\"reply-preview-name\"></div><div class=\"reply-preview-text\"></div>;
    rp.onclick=e=>{e.stopPropagation();scrollToMsg(m.replyTo)};
    wrap.insertBefore(rp,bubble);
  }
  bubble.oncontextmenu=e=>showMsgCtx(e,m.id,wrap);"""

new="""  bubble.oncontextmenu=e=>showMsgCtx(e,m.id,wrap);
  // Reply preview — insert BEFORE bubble inside wrap
  if(m.replyTo){
    const rp=document.createElement('div');rp.className='reply-preview';
    rp.innerHTML=<div class=\"reply-preview-name\"></div><div class=\"reply-preview-text\"></div>;
    rp.onclick=e=>{e.stopPropagation();scrollToMsg(m.replyTo)};
    wrap.appendChild(rp);
  }
  wrap.appendChild(bubble);"""

# Also fix the line that adds bubble later
old2="  wrap.appendChild(bubble);wrap.appendChild(reactRow);wrap.appendChild(meta);"
new2="  wrap.appendChild(reactRow);wrap.appendChild(meta);"

print('fix1:', old in c)
if old in c: c=c.replace(old,new)
print('fix2:', old2 in c)
if old2 in c: c=c.replace(old2,new2)

open('ui/gui.py','w',encoding='utf-8').write(c)
print('Done!')
