f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="const area=document.getElementById('msgs');area.innerHTML='<div \"date-sep\">СЕГОДНЯ</div>';\n  store.messages.forEach"
print('found:', old in c)
idx=c.find("area.innerHTML='<div")
print(repr(c[idx:idx+80]))
