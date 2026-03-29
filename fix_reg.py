f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="if(p.u)peers[id].username=p.u;if(p.b)peers[id].bio=p.b;if(p.a)peers[id].avatar=p.a;"
new="if(p.u)peers[id].username=p.u;if(p.b)peers[id].bio=p.b;if(p.a)peers[id].avatar=p.a;if(p.r)peers[id].registeredAt=p.r;"
if old in c:
    c=c.replace(old,new)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Готово!')
else:
    print('не найдено')
