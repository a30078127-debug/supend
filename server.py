"""Supend PWA Server — чистый переписанный бэкенд."""
import asyncio, json, os, hashlib, time, uuid, mimetypes
from aiohttp import web

users          = {}   # username -> {password, bio, avatar, created_at, sup_balance, ref_code}
online         = {}   # username -> ws
messages       = {}   # chat_id  -> [msg, ...]
groups         = {}   # gid      -> {name, avatar, owner, members:{uid->role}, messages:[]}
media          = {}   # fid      -> (bytes, mime)
exchange_orders = {}  # oid      -> order

def h(p):     return hashlib.sha256(p.encode()).hexdigest()
def cid(a,b): return '_'.join(sorted([a, b]))
def ts():     return int(time.time() * 1000)
def tstr():   return time.strftime('%H:%M')

async def ws_handler(request):
    ws = web.WebSocketResponse(max_msg_size=50*1024*1024, heartbeat=25)
    await ws.prepare(request)
    me = None

    async def send(d):
        try: await ws.send_str(json.dumps(d))
        except: pass

    async def push(to, d):
        w = online.get(to)
        if w:
            try: await w.send_str(json.dumps(d))
            except: pass

    async def push_group(gid, d, exclude=None):
        g = groups.get(gid, {})
        for uid in g.get('members', {}):
            if uid != exclude and uid in online:
                try: await online[uid].send_str(json.dumps(d))
                except: pass

    async for raw in ws:
        if raw.type not in (web.WSMsgType.TEXT, web.WSMsgType.BINARY): break
        try:
            d = json.loads(raw.data)
            c = d.get('cmd')

            if c == 'ping':
                await send({'type': 'pong'}); continue

            # ── Register ──────────────────────────────────────────────────────
            if c == 'register':
                u = d.get('username','').strip().lower()
                p = d.get('password','')
                if not u or not p:
                    await send({'type':'register_error','msg':'Введи логин и пароль'}); continue
                if len(u) < 3 or not u.replace('_','').isalnum():
                    await send({'type':'register_error','msg':'Логин: 3+ букв/цифр/_'}); continue
                if u in users:
                    await send({'type':'register_error','msg':'Логин занят'}); continue
                ref_code = u[:8].upper()
                bonus = 0
                inv = d.get('inv_code','').upper()
                inviter = None
                if inv:
                    for un, ud in users.items():
                        if ud.get('ref_code','') == inv:
                            inviter = un; break
                    if inviter:
                        bonus = 100
                        users[inviter]['sup_balance'] = users[inviter].get('sup_balance',0) + 200
                        await push(inviter, {'type':'ref_reward','amount':200,'from':u})
                users[u] = {
                    'password': h(p), 'bio': d.get('bio',''), 'avatar': d.get('avatar',''),
                    'created_at': time.strftime('%d.%m.%Y'),
                    'sup_balance': 500 + bonus, 'ref_code': ref_code
                }
                me = u; online[u] = ws
                await send({'type':'auth_ok','username':u,'bio':users[u]['bio'],
                    'avatar':users[u]['avatar'],'sup':users[u]['sup_balance'],
                    'ref_code':ref_code,'inv_bonus':bonus,'created_at':users[u]['created_at']})
                continue

            # ── Login ─────────────────────────────────────────────────────────
            if c == 'login':
                u = d.get('username','').strip().lower()
                p = d.get('password','')
                if u not in users:
                    await send({'type':'login_error','msg':'Пользователь не найден'}); continue
                if users[u]['password'] != h(p):
                    await send({'type':'login_error','msg':'Неверный пароль'}); continue
                me = u; online[u] = ws
                ud = users[u]
                await send({'type':'auth_ok','username':u,'bio':ud.get('bio',''),
                    'avatar':ud.get('avatar',''),'sup':ud.get('sup_balance',0),
                    'ref_code':ud.get('ref_code',u[:8].upper()),
                    'created_at':ud.get('created_at','')})
                for ck in messages:
                    if u in ck.split('_'):
                        other = [x for x in ck.split('_') if x != u]
                        if other: await push(other[0], {'type':'user_online','username':u})
                continue

            if not me:
                await send({'type':'error','msg':'Нужна авторизация'}); continue

            # ── Save profile ──────────────────────────────────────────────────
            if c == 'save_profile':
                users[me]['bio'] = d.get('bio','')
                if d.get('avatar'): users[me]['avatar'] = d['avatar']
                for ck in messages:
                    if me in ck.split('_'):
                        other = [x for x in ck.split('_') if x != me]
                        if other: await push(other[0], {'type':'profile_update','username':me,
                            'bio':users[me]['bio'],'avatar':users[me].get('avatar','')})

            # ── Search ────────────────────────────────────────────────────────
            elif c == 'search':
                q = d.get('username','').strip().lower()
                if q in users and q != me:
                    ud = users[q]
                    await send({'type':'search_result','found':True,'username':q,
                        'bio':ud.get('bio',''),'avatar':ud.get('avatar',''),
                        'online':q in online,'created_at':ud.get('created_at','')})
                else:
                    await send({'type':'search_result','found':False})

            # ── Get chats ─────────────────────────────────────────────────────
            elif c == 'get_chats':
                chats = []
                for ck, msgs in messages.items():
                    if me in ck.split('_') and msgs:
                        other = [x for x in ck.split('_') if x != me][0]
                        last = msgs[-1]
                        unread = sum(1 for m in msgs if m['from'] != me and not m.get('read'))
                        lt = last.get('text') or ('🎤' if last.get('mtype')=='voice' else '📷' if last.get('mtype')=='image' else '📎')
                        ud = users.get(other, {})
                        chats.append({'username':other,'last_msg':lt,'last_time':last['time'],
                            'unread':unread,'online':other in online,
                            'avatar':ud.get('avatar',''),'bio':ud.get('bio','')})
                for gid, g in groups.items():
                    if me in g['members'] and g.get('messages'):
                        last = g['messages'][-1]
                        lt = last.get('text') or '📎'
                        unread = sum(1 for m in g['messages'] if m.get('from') != me and not m.get('read'))
                        chats.append({'gid':gid,'name':g['name'],'avatar':g.get('avatar',''),
                            'last_msg':lt,'last_time':last['time'],'unread':unread,'is_group':True,
                            'member_count':len(g['members'])})
                chats.sort(key=lambda x: x.get('last_time',0), reverse=True)
                await send({'type':'chats','chats':chats})

            # ── Get history ───────────────────────────────────────────────────
            elif c == 'get_history':
                w   = d.get('with','')
                gid = d.get('gid','')
                if gid:
                    g = groups.get(gid, {})
                    if me in g.get('members', {}):
                        await send({'type':'history','gid':gid,'messages':g.get('messages',[])[-100:]})
                else:
                    ck = cid(me, w)
                    await send({'type':'history','with':w,'messages':messages.get(ck,[])[-100:]})

            # ── Send message ──────────────────────────────────────────────────
            elif c == 'send_msg':
                to    = d.get('to','')
                gid   = d.get('gid','')
                text  = d.get('text','')
                mtype = d.get('mtype','text')
                url   = d.get('url','')

                if gid:
                    g = groups.get(gid)
                    if not g or me not in g['members']: continue
                    msg = {
                        'id': str(uuid.uuid4()), 'from': me, 'gid': gid,
                        'text': text, 'time': ts(), 'tstr': tstr(),
                        'mtype': mtype, 'url': url,
                        'filename': d.get('filename',''), 'duration': d.get('duration',''),
                        'reply_to': d.get('reply_to'), 'reply_to_text': d.get('reply_to_text',''),
                        'reply_to_name': d.get('reply_to_name',''), 'reactions': {}
                    }
                    g['messages'].append(msg)
                    payload = {'type':'group_msg', 'gid': gid, **msg}
                    await push_group(gid, payload)
                    await send(payload)
                    if mtype == 'text' and text:
                        users[me]['sup_balance'] = users[me].get('sup_balance',0) + max(1, len(text)//50)
                else:
                    if not to or to not in users: continue
                    if mtype == 'text' and not text.strip(): continue
                    ck = cid(me, to)
                    if ck not in messages: messages[ck] = []
                    msg = {
                        'id': str(uuid.uuid4()), 'from': me, 'to': to,
                        'text': text, 'time': ts(), 'tstr': tstr(),
                        'mtype': mtype, 'url': url,
                        'filename': d.get('filename',''), 'duration': d.get('duration',''),
                        'reply_to': d.get('reply_to'), 'reply_to_text': d.get('reply_to_text',''),
                        'reply_to_name': d.get('reply_to_name',''), 'reactions': {}
                    }
                    messages[ck].append(msg)
                    payload = {'type':'message', **msg}
                    if to in online:
                        await push(to, payload)
                        await push(to, {'type':'new_chat','from':me,
                            'avatar':users[me].get('avatar',''),'bio':users[me].get('bio','')})
                    await send(payload)
                    if mtype == 'text' and text:
                        users[me]['sup_balance'] = users[me].get('sup_balance',0) + max(1, len(text)//50)

            # ── Mark read ─────────────────────────────────────────────────────
            elif c == 'mark_read':
                w   = d.get('with','')
                gid = d.get('gid','')
                if gid:
                    for m in groups.get(gid,{}).get('messages',[]):
                        if m.get('from') != me: m['read'] = True
                else:
                    for m in messages.get(cid(me,w),[]):
                        if m['from'] != me: m['read'] = True

            # ── Edit message ──────────────────────────────────────────────────
            elif c == 'edit_msg':
                mid  = d.get('msg_id','')
                text = d.get('text','')
                gid  = d.get('gid','')
                to   = d.get('to','')
                if gid:
                    for m in groups.get(gid,{}).get('messages',[]):
                        if m['id'] == mid and m['from'] == me:
                            m['text'] = text; m['edited'] = True; break
                    await push_group(gid, {'type':'msg_edit','msg_id':mid,'text':text,'gid':gid})
                else:
                    for m in messages.get(cid(me,to),[]):
                        if m['id'] == mid and m['from'] == me:
                            m['text'] = text; m['edited'] = True; break
                    p2 = {'type':'msg_edit','msg_id':mid,'text':text,'from':me}
                    await push(to, p2); await send(p2)

            # ── Delete message ────────────────────────────────────────────────
            elif c == 'delete_msg':
                mid = d.get('msg_id','')
                gid = d.get('gid','')
                to  = d.get('to','')
                if gid:
                    g = groups.get(gid,{})
                    g['messages'] = [m for m in g.get('messages',[]) if not (m['id']==mid and m['from']==me)]
                    await push_group(gid, {'type':'msg_delete','msg_id':mid,'gid':gid})
                else:
                    ck = cid(me, to)
                    messages[ck] = [m for m in messages.get(ck,[]) if not (m['id']==mid and m['from']==me)]
                    p2 = {'type':'msg_delete','msg_id':mid}
                    await push(to, p2); await send(p2)

            # ── Pin message ───────────────────────────────────────────────────
            elif c == 'pin_msg':
                mid = d.get('msg_id','')
                gid = d.get('gid','')
                to  = d.get('to','')
                txt = d.get('text','')
                if gid:
                    g = groups.get(gid,{})
                    if me in g.get('members',{}) and g['members'][me] in ('admin','owner'):
                        g['pinned_id'] = mid; g['pinned_text'] = txt
                        await push_group(gid, {'type':'pin_update','gid':gid,'msg_id':mid,'text':txt})
                else:
                    ck = cid(me, to)
                    for m in messages.get(ck,[]):
                        m.pop('pinned', None)
                        if m['id'] == mid: m['pinned'] = True
                    p2 = {'type':'pin_update','from':me,'msg_id':mid,'text':txt}
                    await push(to, p2); await send(p2)

            # ── React ─────────────────────────────────────────────────────────
            elif c == 'react':
                mid   = d.get('msg_id','')
                emoji = d.get('emoji','')
                gid   = d.get('gid','')
                to    = d.get('to','')
                def apply_react(msg_list):
                    for m in msg_list:
                        if m['id'] == mid:
                            r = m.setdefault('reactions', {})
                            for e in list(r):
                                if me in r[e]: r[e].remove(me)
                                if not r[e]: del r[e]
                            r.setdefault(emoji, []).append(me)
                            return m['reactions']
                    return None
                if gid:
                    rr = apply_react(groups.get(gid,{}).get('messages',[]))
                    if rr is not None:
                        await push_group(gid, {'type':'reaction','msg_id':mid,'gid':gid,'reactions':rr})
                else:
                    ck = cid(me, to)
                    rr = apply_react(messages.get(ck,[]))
                    if rr is not None:
                        p2 = {'type':'reaction','msg_id':mid,'reactions':rr}
                        await push(to, p2); await send(p2)

            # ── Create group ──────────────────────────────────────────────────
            elif c == 'create_group':
                name    = d.get('name','').strip()
                members = d.get('members', [])
                avatar  = d.get('avatar','')
                if not name: continue
                gid = str(uuid.uuid4())[:8]
                member_map = {me: 'owner'}
                for uid in members:
                    if uid in users: member_map[uid] = 'member'
                groups[gid] = {
                    'id': gid, 'name': name, 'avatar': avatar,
                    'owner': me, 'members': member_map,
                    'messages': [], 'pinned_id': None, 'pinned_text': ''
                }
                payload = {'type':'group_created','gid':gid,'name':name,
                    'avatar':avatar,'owner':me,'members':member_map}
                await send(payload)
                for uid in member_map:
                    if uid != me: await push(uid, payload)

            # ── Group actions ─────────────────────────────────────────────────
            elif c == 'group_add_member':
                gid = d.get('gid',''); uid = d.get('uid','')
                g = groups.get(gid)
                if not g or g['members'].get(me) not in ('admin','owner'): continue
                if uid in users:
                    g['members'][uid] = 'member'
                    await push_group(gid, {'type':'group_member_added','gid':gid,'uid':uid})
                    await push(uid, {'type':'group_invited','gid':gid,'name':g['name'],
                        'avatar':g.get('avatar',''),'owner':g['owner'],'members':g['members']})

            elif c == 'group_kick':
                gid = d.get('gid',''); uid = d.get('uid','')
                g = groups.get(gid)
                if not g or g['members'].get(me) not in ('admin','owner'): continue
                if uid == g['owner']: continue
                g['members'].pop(uid, None)
                await push_group(gid, {'type':'group_member_removed','gid':gid,'uid':uid})
                await push(uid, {'type':'group_kicked','gid':gid})

            elif c == 'group_set_role':
                gid = d.get('gid',''); uid = d.get('uid',''); role = d.get('role','member')
                g = groups.get(gid)
                if not g or g.get('owner') != me: continue
                if uid in g['members']:
                    g['members'][uid] = role
                    await push_group(gid, {'type':'group_role_changed','gid':gid,'uid':uid,'role':role})

            elif c == 'group_update':
                gid = d.get('gid','')
                g = groups.get(gid)
                if not g or g['members'].get(me) not in ('admin','owner'): continue
                if d.get('name'):   g['name']   = d['name']
                if d.get('avatar'): g['avatar'] = d['avatar']
                await push_group(gid, {'type':'group_updated','gid':gid,'name':g['name'],'avatar':g.get('avatar','')})

            elif c == 'leave_group':
                gid = d.get('gid','')
                g = groups.get(gid)
                if g and me in g['members']:
                    g['members'].pop(me)
                    await push_group(gid, {'type':'group_member_removed','gid':gid,'uid':me})

            # ── WebRTC ────────────────────────────────────────────────────────
            elif c == 'call_signal':
                to = d.get('to','')
                if to in online:
                    await push(to, {'type':'call_signal','from':me,
                        'signal':d.get('signal',{}),'call_type':d.get('call_type','voice')})

            elif c == 'call_status':
                to = d.get('to','')
                if to in online:
                    await push(to, {'type':'call_status','from':me,'status':d.get('status','')})

            # ── SUP Wallet ────────────────────────────────────────────────────
            elif c == 'get_balance':
                await send({'type':'balance','sup':users[me].get('sup_balance',0)})

            elif c == 'transfer_sup':
                to = d.get('to',''); amt = int(d.get('amount',0))
                if to not in users or amt <= 0: continue
                bal = users[me].get('sup_balance',0)
                if bal < amt:
                    await send({'type':'transfer_error','msg':'Недостаточно SUP'}); continue
                users[me]['sup_balance']  = bal - amt
                users[to]['sup_balance']  = users[to].get('sup_balance',0) + amt
                await send({'type':'transfer_ok','sup':users[me]['sup_balance'],'amount':amt,'to':to})
                await push(to, {'type':'transfer_received','from':me,'amount':amt,'sup':users[to]['sup_balance']})

            # ── P2P Exchange ──────────────────────────────────────────────────
            elif c == 'create_order':
                oid = str(uuid.uuid4())[:8]
                order = {'id':oid,'seller':me,'amount':d.get('amount',0),
                    'price':d.get('price',0),'bank':d.get('bank',''),
                    'card':d.get('card',''),'status':'open','created':ts()}
                exchange_orders[oid] = order
                for u2, w2 in online.items():
                    if u2 != me:
                        try: await w2.send_str(json.dumps({'type':'new_order','order':order}))
                        except: pass
                await send({'type':'order_created','order':order})

            elif c == 'get_orders':
                await send({'type':'orders','orders':list(exchange_orders.values())})

            elif c == 'cancel_order':
                oid = d.get('order_id','')
                o = exchange_orders.get(oid)
                if o and o['seller'] == me:
                    o['status'] = 'cancelled'
                    for u2, w2 in online.items():
                        try: await w2.send_str(json.dumps({'type':'order_cancelled','order_id':oid}))
                        except: pass

            elif c == 'buy_order':
                oid = d.get('order_id','')
                o = exchange_orders.get(oid)
                if not o or o['status'] != 'open' or o['seller'] == me: continue
                o['status'] = 'pending'; o['buyer'] = me
                await push(o['seller'], {'type':'order_deal','order':o,'buyer':me,
                    'buyer_avatar':users[me].get('avatar','')})
                await send({'type':'order_deal_started','order':o})

            elif c == 'confirm_deal':
                oid = d.get('order_id','')
                o = exchange_orders.get(oid)
                if not o or o.get('seller') != me: continue
                amt = o['amount']; buyer = o.get('buyer','')
                if users[me].get('sup_balance',0) < amt:
                    await send({'type':'error','msg':'Недостаточно SUP'}); continue
                users[me]['sup_balance'] -= amt
                if buyer in users: users[buyer]['sup_balance'] = users[buyer].get('sup_balance',0) + amt
                o['status'] = 'closed'
                await send({'type':'deal_confirmed','order_id':oid,'sup':users[me]['sup_balance']})
                if buyer in users:
                    await push(buyer, {'type':'deal_confirmed','order_id':oid,
                        'sup':users[buyer]['sup_balance'],'amount':amt})

        except Exception as e:
            print(f'WS err: {e}')

    if me:
        online.pop(me, None)
        for ck in messages:
            if me in ck.split('_'):
                other = [x for x in ck.split('_') if x != me]
                if other and other[0] in online:
                    asyncio.create_task(push(other[0], {'type':'user_offline','username':me}))
    return ws

# ── HTTP ──────────────────────────────────────────────────────────────────────
async def index_handler(request):
    return web.Response(text=open('index.html',encoding='utf-8').read(), content_type='text/html')

async def upload_handler(request):
    try:
        reader = await request.multipart()
        field  = await reader.next()
        if not field: raise web.HTTPBadRequest()
        filename = field.filename or 'file'
        data = await field.read()
        # Получаем MIME из заголовка
        mime = field.headers.get('Content-Type','application/octet-stream')
        # Нормализуем MIME для аудио
        if 'webm' in mime:   mime = 'audio/webm'
        elif 'mp4' in mime and 'video' not in mime: mime = 'audio/mp4'
        elif 'ogg' in mime:  mime = 'audio/ogg'
        elif 'mpeg' in mime or 'mp3' in mime: mime = 'audio/mpeg'
        # Определяем расширение
        ext_map = {
            'audio/webm': '.webm', 'audio/mp4': '.mp4', 'audio/ogg': '.ogg',
            'audio/mpeg': '.mp3', 'image/jpeg': '.jpg', 'image/png': '.png',
            'image/gif': '.gif', 'image/webp': '.webp', 'video/mp4': '.mp4',
            'video/webm': '.webm',
        }
        ext = ext_map.get(mime) or os.path.splitext(filename)[1] or '.bin'
        fid = str(uuid.uuid4()) + ext
        media[fid] = (data, mime)
        print(f'[UPLOAD] {fid} mime={mime} size={len(data)}')
        return web.Response(text=json.dumps({'url':f'/media/{fid}'}), content_type='application/json')
    except Exception as e:
        print(f'Upload err: {e}'); raise web.HTTPInternalServerError()

async def media_handler(request):
    fid = request.match_info['fid']
    if fid not in media: raise web.HTTPNotFound()
    data, mime = media[fid]
    # Accept-Ranges нужен для Safari чтобы воспроизводить аудио
    headers = {
        'Cache-Control': 'public,max-age=86400',
        'Accept-Ranges': 'bytes',
        'Access-Control-Allow-Origin': '*',
    }
    return web.Response(body=data, content_type=mime, headers=headers)

async def manifest_handler(request):
    m = {"name":"Supend","short_name":"Supend","start_url":"/","display":"standalone",
         "background_color":"#ffffff","theme_color":"#1ABC9C",
         "icons":[{"src":"/icon.png","sizes":"192x192","type":"image/png"},
                  {"src":"/icon.png","sizes":"512x512","type":"image/png"}]}
    return web.Response(text=json.dumps(m), content_type='application/json')

async def icon_handler(request):
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect width="192" height="192" rx="40" fill="#1ABC9C"/><text x="96" y="130" font-size="100" text-anchor="middle" fill="white" font-family="Arial">S</text></svg>'
    return web.Response(body=svg, content_type='image/svg+xml')

async def main():
    port = int(os.environ.get('PORT', 8080))
    app  = web.Application(client_max_size=50*1024*1024)
    app.router.add_get('/',             index_handler)
    app.router.add_get('/ws',           ws_handler)
    app.router.add_post('/upload',      upload_handler)
    app.router.add_get('/media/{fid}',  media_handler)
    app.router.add_get('/manifest.json',manifest_handler)
    app.router.add_get('/icon.png',     icon_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f'[*] Supend PWA на порту {port}')
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
