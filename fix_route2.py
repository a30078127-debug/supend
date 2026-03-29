f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="app.router.add_get('/', self._index)\n        app.router.add_get('/ws', self._ws_handler)"
new="app.router.add_get('/', self._index)\n        app.router.add_get('/manifest.json', self._manifest)\n        app.router.add_get('/ws', self._ws_handler)"
print('found:', old in c)
if old in c:
    c=c.replace(old,new,1)
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
