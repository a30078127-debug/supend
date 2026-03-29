f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()

# Найдём и покажем блок с tracker в run()
idx=c.find('start_relay_listener')
print(repr(c[idx-50:idx+400]))
