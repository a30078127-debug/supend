f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old='<meta charset="UTF-8">'
new='<meta charset="UTF-8">\n<link rel="manifest" href="/manifest.json">\n<meta name="theme-color" content="#1ABC9C">\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-title" content="Supend">'
if old in c and 'manifest.json' not in c:
    c=c.replace(old,new,1)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
else:
    print('not found or already done')
