"""Supend Web Server."""
import asyncio, json, os, hashlib, time, uuid, base64, mimetypes
from aiohttp import web

users = {}
online = {}
messages = {}
media = {}

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def cid(a, b): return '_'.join(sorted([a, b]))
def ts(): return int(time.time() * 1000)

async def ws_handler(request):
    ws = web.WebSocketResponse(max_msg_size=50*1024*1024)
    await ws.prepare(request)
    me = None

    async def send(d):
        try: await ws.send_str(json.dumps(d))
        except: pass

    async def push(to, d):
        if to in online:
            try: await online[to].send_str(json.dumps(d))
            except: pass

    async for raw in ws:
        if raw.type not in (web.WSMsgType.TEXT, web.WSMsgType.BINARY): break
        try:
            d = json.loads(raw.data)
            c = d.get('cmd')

            if c == 'ping':
                await send({'type': 'pong'})
                continue

            if c == 'register':
                u = d['username'].strip().lower()
                p = d['password']
                if not u or not p: await send({'type':'register_error','msg':'Введи логин и пароль'}); continue
                if len(u) < 3 or not u.replace('_','').isalnum(): await send({'type':'register_error','msg':'Логин: 3+ букв/цифр/_'}); continue
                if u in users: await send({'type':'register_error','msg':'Логин занят'}); continue
                users[u] = {'password':hash_pw(p),'bio':d.get('bio',''),'avatar':d.get('avatar',''),'created_at':ts()}
                me = u; online[u] = ws
                await send({'type':'auth_ok','username':u,'bio':users[u]['bio'],'avatar':users[u]['avatar']})

            elif c == 'login':
                u = d['username'].strip().lower(); p = d['password']
                if u not in users: await send({'type':'login_error','msg':'Пользователь не найден'}); continue
                if users[u]['password'] != hash_pw(p): await send({'type':'login_error','msg':'Неверный пароль'}); continue
                me = u; online[u] = ws
                await send({'type':'auth_ok','username':u,'bio':users[u]['bio'],'avatar':users[u]['avatar']})
                for ck in messages:
                    if u in ck.split('_'):
                        other = [x for x in ck.split('_') if x != u]
                        if other: await push(other[0], {'type':'user_online','username':u})

            elif c == 'save_profile':
                if not me: continue
                users[me]['bio'] = d.get('bio','')
                if d.get('avatar'): users[me]['avatar'] = d['avatar']

            elif c == 'search':
                if not me: continue
                q = d.get('username','').strip().lower()
                if q in users and q != me:
                    await send({'type':'search_result','found':True,'username':q,'bio':users[q].get('bio',''),'avatar':users[q].get('avatar',''),'online':q in online})
                else:
                    await send({'type':'search_result','found':False})

            elif c == 'send_msg':
                if not me: continue
                to = d.get('to','')
                if not to or to not in users: continue
                msg_type = d.get('type','text')
                text = d.get('text','')
                if msg_type == 'text' and not text.strip(): continue
                url = d.get('url','')
                ck = cid(me, to)
                if ck not in messages: messages[ck] = []
                msg = {'id':str(uuid.uuid4()),'from':me,'to':to,'text':text,'time':ts(),
                       'type':msg_type,'url':url,'filename':d.get('filename',''),
                       'duration':d.get('duration',''),'reply_to':d.get('reply_to'),
                       'reply_to_text':d.get('reply_to_text','')}
                messages[ck].append(msg)
                await send({'type':'message',**msg})
                await push(to, {'type':'message',**msg})

            elif c == 'get_history':
                if not me: continue
                w = d.get('with',''); ck = cid(me,w)
                await send({'type':'history','with':w,'messages':messages.get(ck,[])[-100:]})

            elif c == 'get_chats':
                if not me: continue
                chats = []
                for ck, msgs in messages.items():
                    if me in ck.split('_') and msgs:
                        other = [x for x in ck.split('_') if x != me][0]
                        last = msgs[-1]
                        unread = sum(1 for m in msgs if m['from']!=me and not m.get('read'))
                        lt = last['text'] or ('🎤' if last['type']=='voice' else '📷' if last['type']=='image' else '📎')
                        chats.append({'username':other,'last_msg':lt,'last_time':last['time'],'unread':unread,
                                      'online':other in online,'avatar':users.get(other,{}).get('avatar',''),'bio':users.get(other,{}).get('bio','')})
                chats.sort(key=lambda x:x['last_time'],reverse=True)
                await send({'type':'chats','chats':chats})

            elif c == 'mark_read':
                if not me: continue
                ck = cid(me, d.get('with',''))
                for m in messages.get(ck,[]): 
                    if m['from'] != me: m['read'] = True

            elif c == 'call_signal':
                if not me: continue
                await push(d.get('to',''), {'type':'call_signal','from':me,'signal':d.get('signal'),'call_type':d.get('call_type','voice')})

            elif c == 'call_status':
                if not me: continue
                await push(d.get('to',''), {'type':'call_status','from':me,'status':d.get('status')})

        except Exception as e:
            print(f'WS err: {e}')

    if me:
        online.pop(me, None)
        for ck in messages:
            if me in ck.split('_'):
                other = [x for x in ck.split('_') if x != me]
                if other: await push(other[0], {'type':'user_offline','username':me})
    return ws

async def index_handler(request):
    return web.Response(text=open('index.html',encoding='utf-8').read(), content_type='text/html')

async def media_handler(request):
    fid = request.match_info['fid']
    if fid not in media: raise web.HTTPNotFound()
    data, mime = media[fid]
    return web.Response(body=data, content_type=mime, headers={'Cache-Control':'public,max-age=86400'})

async def upload_handler(request):
    try:
        reader = await request.multipart()
        field = await reader.next()
        if not field:
            raise web.HTTPBadRequest()
        filename = field.filename or 'file'
        data = await field.read()
        mime = field.headers.get('Content-Type', 'application/octet-stream')
        ext = os.path.splitext(filename)[1] or mimetypes.guess_extension(mime) or '.bin'
        fid = str(uuid.uuid4()) + ext
        media[fid] = (data, mime)
        return web.Response(text=json.dumps({'url': f'/media/{fid}'}), content_type='application/json')
    except Exception as e:
        print(f'Upload err: {e}')
        raise web.HTTPInternalServerError()


    m = {"name":"Supend","short_name":"Supend","start_url":"/","display":"standalone",
         "background_color":"#ffffff","theme_color":"#1ABC9C",
         "icons":[{"src":"/icon.png","sizes":"192x192","type":"image/png"}]}
    return web.Response(text=json.dumps(m), content_type='application/json')

async def main():
    port = int(os.environ.get('PORT', 8080))
    app = web.Application(client_max_size=50*1024*1024)
    app.router.add_get('/', index_handler)
    app.router.add_get('/ws', ws_handler)
    app.router.add_post('/upload', upload_handler)
    app.router.add_get('/media/{fid}', media_handler)
    app.router.add_get('/manifest.json', manifest_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f'[*] Supend на порту {port}')
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
