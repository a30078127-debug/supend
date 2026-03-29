f=open('ui/gui.py',encoding='utf-8')
lines=f.readlines()
f.close()
for i,l in enumerate(lines[5385:5395],5386):
    print(i, repr(l))
