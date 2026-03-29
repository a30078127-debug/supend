f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
import re
fns=[m.group(1) for m in re.finditer(r'function (hide\w+|close\w+Ctx\w*|hidePeer\w*)\(',c)]
print(fns)
