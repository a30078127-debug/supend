f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
manifest="""    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1ABC9C">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Supend">"""
old='    <meta charset="UTF-8">'
new='    <meta charset="UTF-8">\n'+manifest
if old in c and 'manifest.json' not in c:
    c=c.replace(old,new,1)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('already done or not found')
