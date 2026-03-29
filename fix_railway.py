f=open('main.py',encoding='utf-8')
c=f.read()
f.close()
old='webbrowser.open(url)'
new='import os\n    if not os.environ.get("RAILWAY_ENVIRONMENT"): webbrowser.open(url)'
if old in c:
    c=c.replace(old,new)
    open('main.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('already fixed')
