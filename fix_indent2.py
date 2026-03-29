f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="        real_text=text\n            if text.startswith('__MSG__'):"
new="            real_text=text\n            if text.startswith('__MSG__'):"
print('found:', old in c)
if old in c:
    c=c.replace(old,new)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('not found')
