f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="    rp.onclick=e=>{e.stopPropagation();scrollToMsg(m.replyTo)};\n    wrap.insertBefore(rp,bubble);\n  }"
new="    rp.onclick=e=>{e.stopPropagation();scrollToMsg(m.replyTo)};\n    wrap.appendChild(rp);\n  }\n  wrap.appendChild(bubble);"
old2="  wrap.appendChild(reactRow);wrap.appendChild(meta);"
new2="  wrap.appendChild(reactRow);wrap.appendChild(meta);"
print('fix1:', old in c)
if old in c: c=c.replace(old,new)
open('ui/gui.py','w',encoding='utf-8').write(c)
print('Done!')
