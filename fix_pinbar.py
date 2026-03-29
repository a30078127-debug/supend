f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="area.innerHTML='<div class=\"date-sep\">СЕГОДНЯ</div>';\n          store.messages.f"
new="area.innerHTML='<div class=\"date-sep\">СЕГОДНЯ</div>';\n  setTimeout(updatePinnedBar,50);\n          store.messages.f"
if old in c:
    c=c.replace(old,new)
    f=open('ui/gui.py','w',encoding='utf-8')
    f.write(c)
    f.close()
    print('Готово!')
else:
    print('не найдено')
