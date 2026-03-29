f=open('ui/gui.py',encoding='utf-8')
c=f.read()
f.close()
old="app.router.add_get('/', self._index)\n        app.router.add_get('/ws', self._ws_handler)"
new="app.router.add_get('/', self._index)\n        app.router.add_get('/manifest.json', self._manifest)\n        app.router.add_get('/ws', self._ws_handler)"
print('found:', old in c)
if old in c and '/manifest.json' not in c:
    c=c.replace(old,new,1)
    idx=c.find('    async def _index')
    handler="""
    async def _manifest(self, request):
        import json as _mj
        m={"name":"Supend Messenger","short_name":"Supend","start_url":"/","display":"standalone","background_color":"#ffffff","theme_color":"#1ABC9C","icons":[{"src":"/icon.png","sizes":"192x192","type":"image/png"},{"src":"/icon.png","sizes":"512x512","type":"image/png"}]}
        return web.Response(text=_mj.dumps(m),content_type="application/json")

"""
    c=c[:idx]+handler+c[idx:]
    open('ui/gui.py','w',encoding='utf-8').write(c)
    print('Done!')
