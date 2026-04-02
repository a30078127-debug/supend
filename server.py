"""Supend PWA Server — чистый переписанный бэкенд."""
import asyncio, json, os, hashlib, time, uuid, mimetypes, base64, struct
import urllib.request, urllib.error, urllib.parse
from aiohttp import web

users           = {}   # username -> {password, bio, avatar, ...}
online          = {}   # username -> ws
messages        = {}   # chat_id  -> [msg, ...]
groups          = {}   # gid      -> {name, avatar, owner, members, messages}
media           = {}   # fid      -> (bytes, mime)
exchange_orders = {}   # oid      -> order
push_subs       = {}   # username -> [subscription, ...]  (Web Push subscriptions)
stories         = {}   # username -> [{id, media, type, ts, views:[username,...]}]

# VAPID ключи — генерируются один раз при старте
VAPID_PUBLIC  = 'BEROCON9Z0x27j4XwIZeBv2dtUxFpM9sy5HGPlPu6VYaqb_BhjFJzA37MmmpCr0LiHf6SZ_wrE82SsTOBW1Nc_o'
VAPID_PRIVATE = 'Os9S2QtWUy3LeVMGGzFjOnpbJqOz5AEqqy2dI_3tdm8'
VAPID_SUBJECT = 'mailto:supend@supend.app'

def h(p):     return hashlib.sha256(p.encode()).hexdigest()
def cid(a,b): return '_'.join(sorted([a, b]))
def ts():     return int(time.time() * 1000)
def tstr():   return time.strftime('%H:%M')

def b64url_decode(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

def b64url_encode(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def make_vapid_jwt(audience):
    """Создаём VAPID JWT для авторизации push."""
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
        from cryptography.hazmat.backends import default_backend
        import hashlib as _hl

        header  = b64url_encode(json.dumps({'typ':'JWT','alg':'ES256'}).encode())
        payload = b64url_encode(json.dumps({
            'aud': audience,
            'exp': int(time.time()) + 86400,
            'sub': VAPID_SUBJECT
        }).encode())
        signing_input = f'{header}.{payload}'.encode()

        priv_int = int.from_bytes(b64url_decode(VAPID_PRIVATE), 'big')
        key = ec.derive_private_key(priv_int, ec.SECP256R1(), default_backend())
        from cryptography.hazmat.primitives import hashes
        sig_der = key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(sig_der)
        sig = r.to_bytes(32,'big') + s.to_bytes(32,'big')
        return f'{header}.{payload}.{b64url_encode(sig)}'
    except Exception as ex:
        print(f'[VAPID JWT] {ex}')
        return None

async def send_web_push(subscription, payload_dict):
    """Отправляем Web Push через pywebpush."""
    try:
        from pywebpush import webpush, WebPushException
        import asyncio
        payload_str = json.dumps(payload_dict)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: webpush(
            subscription_info   = subscription,
            data                = payload_str,
            vapid_private_key   = VAPID_PRIVATE,
            vapid_claims        = {'sub': VAPID_SUBJECT},
            content_encoding    = 'aes128gcm',
            ttl                 = 86400,
        ))
        print(f'[Push] ✅ sent to {subscription["endpoint"][:50]}')
    except Exception as ex:
        print(f'[Push] ❌ error: {ex}')

async def push_notif(username, title, body, tag='supend'):
    """Отправляем push всем подпискам пользователя."""
    subs = push_subs.get(username, [])
    if not subs:
        return
    payload = {'title': title, 'body': body, 'tag': tag, 'icon': '/logo', 'badge': '/logo'}
    dead = []
    for sub in subs:
        try:
            await send_web_push(sub, payload)
        except Exception as ex:
            print(f'[Push] dead sub: {ex}')
            dead.append(sub)
    for d in dead:
        subs.remove(d)

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
                inv_bonus = 0   # бонус новому пользователю за ввод чужого кода
                inviter = None
                inv = d.get('inv_code','').strip().upper()
                if inv:
                    # Ищем владельца этого реф-кода среди существующих пользователей
                    for un, ud in users.items():
                        if ud.get('ref_code','').upper() == inv:
                            inviter = un; break
                    if inviter:
                        inv_bonus = 100  # новый пользователь получает 100
                        # Пригласившему — 200
                        users[inviter]['sup_balance'] = users[inviter].get('sup_balance', 0) + 200
                        await push(inviter, {'type':'ref_reward','amount':200,'from':u})
                users[u] = {
                    'password': h(p), 'bio': d.get('bio',''), 'avatar': d.get('avatar',''),
                    'created_at': time.strftime('%d.%m.%Y'),
                    'sup_balance': inv_bonus,  # стартовый баланс = только реф-бонус (или 0)
                    'ref_code': ref_code,
                    'username': u
                }
                me = u; online[u] = ws
                await send({'type':'auth_ok','username':u,'bio':users[u]['bio'],
                    'avatar':users[u]['avatar'],'sup':users[u]['sup_balance'],
                    'ref_code':ref_code,'inv_bonus':inv_bonus,'created_at':users[u]['created_at']})
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
                if d.get('status'): users[me]['status'] = d['status']
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
                            'avatar':ud.get('avatar',''),'bio':ud.get('bio',''),
                            'status':ud.get('status','online'),
                            'last_seen':ud.get('last_seen',0)})
                for gid, g in groups.items():
                    if me not in g['members']: continue
                    # Группа показывается даже без сообщений
                    my_role_data = g['members'].get(me, 'member')
                    my_role = my_role_data if isinstance(my_role_data, str) else my_role_data.get('role', 'member')
                    if g.get('messages'):
                        last = g['messages'][-1]
                        lt = last.get('text') or ('🎤' if last.get('mtype')=='voice' else '📷' if last.get('mtype')=='image' else '📎')
                        unread = sum(1 for m in g['messages'] if m.get('from') != me and not m.get('read'))
                        last_time = last['time']
                    else:
                        lt = 'Группа создана'; unread = 0; last_time = ts()
                    chats.append({'gid':gid,'name':g['name'],'avatar':g.get('avatar',''),
                        'desc':g.get('desc',''),'last_msg':lt,'last_time':last_time,
                        'unread':unread,'is_group':True,'member_count':len(g['members']),
                        'my_role':my_role,'owner':g.get('owner','')})
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
                    else:
                        # Пользователь офлайн — Web Push уведомление
                        sender_name = '@' + me
                        body_text = text if mtype == 'text' else ('🎤 Голосовое' if mtype=='voice' else '📷 Фото' if mtype=='image' else '📎 Файл')
                        asyncio.create_task(push_notif(to, sender_name, body_text[:80], f'msg-{me}'))
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


            # ── Stories ───────────────────────────────────────────────────────
            elif c == 'post_story':
                media_data = d.get('media', '')
                mtype = d.get('mtype', 'image')  # 'image' or 'video'
                now = int(time.time())
                sid = str(uuid.uuid4())[:8]
                if me not in stories:
                    stories[me] = []
                # Удаляем истории старше 24 часов
                stories[me] = [s for s in stories[me] if now - s['ts'] < 86400]
                stories[me].append({'id': sid, 'media': media_data, 'type': mtype, 'ts': now, 'views': []})
                await send({'type': 'story_posted', 'story_id': sid})
                # Уведомляем тех кто онлайн и переписывался с нами
                for u, w in list(online.items()):
                    if u == me: continue
                    ch = messages.get(cid(me, u))
                    if ch:  # есть переписка
                        try:
                            await w.send_str(json.dumps({
                                'type': 'story_new',
                                'username': me,
                                'avatar': users[me].get('avatar',''),
                                'story_id': sid
                            }))
                        except: pass

            elif c == 'get_stories':
                # Получаем истории всех пользователей с которыми есть переписка
                now = int(time.time())
                result = []
                for u in list(users.keys()):
                    if u == me: continue
                    ch = messages.get(cid(me, u))
                    if not ch: continue
                    user_stories = [s for s in stories.get(u, []) if now - s['ts'] < 86400]
                    if user_stories:
                        result.append({
                            'username': u,
                            'avatar': users[u].get('avatar',''),
                            'stories': [{'id': s['id'], 'type': s['type'], 'ts': s['ts']} for s in user_stories]
                        })
                # Добавляем свои истории
                my_stories = [s for s in stories.get(me, []) if now - s['ts'] < 86400]
                await send({'type': 'stories_list', 'peers': result, 'my': my_stories})

            elif c == 'get_story_media':
                # Получить медиа конкретной истории
                username = d.get('username', me)
                sid = d.get('story_id')
                now = int(time.time())
                user_stories = [s for s in stories.get(username, []) if now - s['ts'] < 86400]
                story = next((s for s in user_stories if s['id'] == sid), None)
                if story:
                    # Отмечаем просмотр
                    if me not in story['views'] and me != username:
                        story['views'].append(me)
                    await send({'type': 'story_media', 'story_id': sid, 'username': username,
                                'media': story['media'], 'mtype': story['type'],
                                'ts': story['ts'], 'views': story['views']})
                else:
                    await send({'type': 'story_media', 'story_id': sid, 'error': True})

            elif c == 'get_my_story_views':
                sid = d.get('story_id')
                my_s = next((s for s in stories.get(me, []) if s['id'] == sid), None)
                if my_s:
                    viewers = []
                    for v in my_s['views']:
                        viewers.append({'username': v, 'avatar': users.get(v,{}).get('avatar','')})
                    await send({'type': 'story_views', 'story_id': sid, 'views': viewers, 'count': len(viewers)})

            elif c == 'delete_story':
                sid = d.get('story_id')
                if me in stories:
                    stories[me] = [s for s in stories[me] if s['id'] != sid]
                await send({'type': 'story_deleted', 'story_id': sid})

            # ── Push subscription ─────────────────────────────────────────────
            elif c == 'push_subscribe':
                sub = d.get('subscription')
                if sub and sub.get('endpoint') and sub.get('keys'):
                    subs = push_subs.setdefault(me, [])
                    # Не дублируем
                    endpoints = [s['endpoint'] for s in subs]
                    if sub['endpoint'] not in endpoints:
                        subs.append(sub)
                    await send({'type':'push_subscribed'})


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
                desc    = d.get('desc','')
                if not name: continue
                gid = str(uuid.uuid4())[:8]
                member_map = {me: {'role':'owner'}}
                for uid in members:
                    if uid in users: member_map[uid] = {'role':'member'}
                # Системное сообщение о создании
                me_uname = users.get(me,{}).get('username', me)
                sys_msg = {
                    'id': str(uuid.uuid4()), 'from': me, 'gid': gid,
                    'text': f'создал группу «{name}»', 'time': ts(), 'tstr': tstr(),
                    'mtype': 'system', 'url': '', 'filename': '', 'duration': '',
                    'reply_to': None, 'reply_to_text': '', 'reply_to_name': '', 'reactions': {},
                    'system': True, 'system_actor': me_uname
                }
                groups[gid] = {
                    'id': gid, 'name': name, 'avatar': avatar, 'desc': desc,
                    'owner': me, 'members': member_map,
                    'messages': [sys_msg], 'pinned_id': None, 'pinned_text': ''
                }
                # Добавляем системные сообщения о приглашении участников
                for uid in members:
                    if uid in users:
                        uid_uname = users.get(uid,{}).get('username', uid)
                        inv_msg = {
                            'id': str(uuid.uuid4()), 'from': me, 'gid': gid,
                            'text': f'пригласил {uid_uname}', 'time': ts()+1, 'tstr': tstr(),
                            'mtype': 'system', 'url': '', 'filename': '', 'duration': '',
                            'reply_to': None, 'reply_to_text': '', 'reply_to_name': '', 'reactions': {},
                            'system': True, 'system_actor': me_uname, 'system_target': uid_uname
                        }
                        groups[gid]['messages'].append(inv_msg)
                roles_simple = {uid: (v if isinstance(v,str) else v.get('role','member')) for uid,v in member_map.items()}
                payload = {'type':'group_created','gid':gid,'name':name,
                    'avatar':avatar,'desc':desc,'owner':me,
                    'members':roles_simple, 'my_role':'owner'}
                await send(payload)
                for uid in member_map:
                    if uid != me and uid in online:
                        await push(uid, {**payload, 'my_role':'member'})

            # ── Group actions ─────────────────────────────────────────────────
            elif c == 'group_add_member':
                gid = d.get('gid',''); uid = d.get('uid','')
                g = groups.get(gid)
                if not g or g['members'].get(me) not in ({'owner','admin'} | set()): 
                    # check role properly
                    my_role_d = g['members'].get(me, 'member') if g else 'member'
                    my_role_v = my_role_d if isinstance(my_role_d, str) else my_role_d.get('role','member')
                    if my_role_v not in ('admin','owner'): continue
                if uid in users:
                    g['members'][uid] = {'role':'member'}
                    # Системное сообщение о добавлении
                    me_uname = users.get(me,{}).get('username', me)
                    uid_uname = users.get(uid,{}).get('username', uid)
                    sys_msg = {
                        'id': str(uuid.uuid4()), 'from': me, 'gid': gid,
                        'text': f'пригласил {uid_uname}', 'time': ts(), 'tstr': tstr(),
                        'mtype': 'system', 'url': '', 'filename': '', 'duration': '',
                        'reply_to': None, 'reply_to_text': '', 'reply_to_name': '', 'reactions': {},
                        'system': True, 'system_actor': me_uname, 'system_target': uid_uname
                    }
                    g['messages'].append(sys_msg)
                    payload_sys = {'type':'group_msg', 'gid': gid, **sys_msg}
                    await push_group(gid, payload_sys)
                    await push_group(gid, {'type':'group_member_added','gid':gid,'uid':uid})
                    await push(uid, {'type':'group_invited','gid':gid,'name':g['name'],
                        'avatar':g.get('avatar',''),'owner':g['owner'],'members':{
                            k: (v if isinstance(v,str) else v.get('role','member')) for k,v in g['members'].items()
                        }})

            elif c == 'group_kick':
                gid = d.get('gid',''); uid = d.get('uid','')
                g = groups.get(gid)
                if not g or g['members'].get(me) not in ('admin','owner'): continue
                if uid == g['owner']: continue
                g['members'].pop(uid, None)
                await push_group(gid, {'type':'group_member_removed','gid':gid,'uid':uid})
                await push(uid, {'type':'group_kicked','gid':gid})

            elif c == 'get_group_info':
                gid = d.get('gid','')
                g = groups.get(gid)
                if not g or me not in g.get('members',{}): continue
                my_role = g['members'].get(me, {})
                if isinstance(my_role, dict): my_role = my_role.get('role','member')
                # Build members with username from users dict
                members_out = {}
                for uid, role_data in g['members'].items():
                    role = role_data if isinstance(role_data, str) else role_data.get('role','member')
                    ud = users.get(uid, {})
                    members_out[uid] = {
                        'username': ud.get('username', uid),
                        'avatar': ud.get('avatar',''),
                        'role': role,
                        'rights': role_data.get('rights',{}) if isinstance(role_data, dict) else {}
                    }
                await send({'type':'group_info','gid':gid,'name':g['name'],
                    'avatar':g.get('avatar',''),'desc':g.get('desc',''),
                    'owner':g.get('owner',''),'my_role':my_role,
                    'members':members_out,'member_count':len(members_out)})


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
                o['status'] = 'pending'; o['buyer'] = me; o['deal_status'] = 'waiting_payment'
                if not o.get('chat_msgs'): o['chat_msgs'] = []
                await push(o['seller'], {'type':'order_deal','order':o,'buyer':me,
                    'buyer_avatar':users[me].get('avatar','')})
                await send({'type':'order_deal_started','order_id':oid,'order':o})

            elif c == 'deal_paid':
                oid = d.get('order_id','')
                o = exchange_orders.get(oid)
                if not o or o.get('buyer') != me: continue
                o['deal_status'] = 'paid'
                await push(o['seller'], {'type':'deal_status','order_id':oid,'deal_status':'paid'})
                await send({'type':'deal_status','order_id':oid,'deal_status':'paid'})

            elif c == 'deal_dispute':
                oid = d.get('order_id','')
                o = exchange_orders.get(oid)
                if not o or o.get('seller') != me: continue
                o['deal_status'] = 'dispute'
                buyer = o.get('buyer','')
                await push(buyer, {'type':'deal_status','order_id':oid,'deal_status':'dispute'})
                await send({'type':'deal_status','order_id':oid,'deal_status':'dispute'})

            elif c == 'deal_chat_msg':
                oid  = d.get('order_id','')
                text = d.get('text','').strip()
                o    = exchange_orders.get(oid)
                if not o or not text: continue
                if me not in (o.get('seller',''), o.get('buyer','')): continue
                partner = o.get('buyer') if me == o.get('seller') else o.get('seller')
                msg = {'from':me,'text':text,'time':tstr()}
                if not o.get('chat_msgs'): o['chat_msgs'] = []
                o['chat_msgs'].append(msg)
                await push(partner, {'type':'deal_chat_msg','order_id':oid,'from':me,'text':text,'time':tstr()})
                await send({'type':'deal_chat_msg','order_id':oid,'from':me,'text':text,'time':tstr()})

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
        users[me]['last_seen'] = ts()  # сохраняем время последнего визита
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
    logo_path = 'logo.jpg'
    icon_type = 'image/jpeg' if os.path.exists(logo_path) else 'image/svg+xml'
    m = {"name":"Supend","short_name":"Supend","start_url":"/","display":"standalone",
         "background_color":"#1ABC9C","theme_color":"#1ABC9C",
         "icons":[
             {"src":"/logo","sizes":"192x192","type":icon_type,"purpose":"any"},
             {"src":"/logo","sizes":"512x512","type":icon_type,"purpose":"any"},
             {"src":"/icon.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},
             {"src":"/icon.png","sizes":"512x512","type":"image/png","purpose":"any maskable"},
         ]}
    return web.Response(text=json.dumps(m), content_type='application/json',
                        headers={'Cache-Control':'no-cache'})

async def vapid_handler(request):
    return web.Response(
        text=json.dumps({'publicKey': VAPID_PUBLIC}),
        content_type='application/json'
    )

async def sw_handler(request):
    try:
        with open('sw.js', 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='application/javascript',
                          headers={'Cache-Control': 'no-cache', 'Service-Worker-Allowed': '/'})
    except FileNotFoundError:
        return web.Response(text='// SW not found', content_type='application/javascript')

async def logo_handler(request):
    logo_path = 'logo.jpg'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            data = f.read()
        return web.Response(body=data, content_type='image/jpeg',
                          headers={'Cache-Control':'public,max-age=86400'})
    # Fallback — красивый SVG с буквой S
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
        '<rect width="512" height="512" rx="112" fill="#1ABC9C"/>'
        '<text x="256" y="360" font-size="320" font-weight="bold" '
        'text-anchor="middle" fill="white" font-family="Arial,sans-serif">S</text>'
        '</svg>'
    ).encode('utf-8')
    return web.Response(body=svg, content_type='image/svg+xml',
                        headers={'Cache-Control':'public,max-age=3600'})

# Логотип встроен как base64 PNG 192x192
_ICON_PNG_B64 = "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"
_ICON_PNG_DATA = None

async def icon_png_handler(request):
    global _ICON_PNG_DATA
    if _ICON_PNG_DATA is None:
        import base64 as _b64
        _ICON_PNG_DATA = _b64.b64decode(_ICON_PNG_B64)
    return web.Response(body=_ICON_PNG_DATA, content_type='image/png',
                       headers={'Cache-Control':'public,max-age=86400'})

async def translate_handler(request):
    try:
        body = await request.json()
        text = body.get('text', '').strip()
        lang = body.get('lang', 'en')
        if not text:
            return web.Response(text=json.dumps({'result': ''}), content_type='application/json')
        import urllib.parse
        encoded = urllib.parse.quote(text)
        url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang}&dt=t&q={encoded}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            translated = ''.join(part[0] for part in data[0] if part and part[0])
        return web.Response(text=json.dumps({'result': translated}), content_type='application/json')
    except Exception as e:
        print(f'[translate] error: {e}')
        return web.Response(text=json.dumps({'result': f'Ошибка перевода: {str(e)}'}), content_type='application/json')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

async def smart_replies_handler(request):
    if not GEMINI_API_KEY:
        return web.Response(text=json.dumps({'replies': []}), content_type='application/json')
    try:
        body = await request.json()
        message = body.get('message', '').strip()
        if not message or len(message) > 500:
            return web.Response(text=json.dumps({'replies': []}), content_type='application/json')

        prompt = (
            f"Message: \"{message}\"\n\n"
            "You are a smart reply assistant. Generate 3-4 very short reply options (max 5 words each) in the SAME LANGUAGE as the message. "
            "Only suggest replies if the message is a question or conversational (needs a response). "
            "If the message is just a statement that doesn't need a reply, return empty list. "
            "Return ONLY a JSON array of strings, nothing else. Example: [\"Yes!\", \"Not sure\", \"Tell me more\"]"
        )

        api_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}'
        payload = json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 100}
        }).encode()

        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        # Extract text from response
        text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        # Clean markdown if present
        text = text.replace('```json', '').replace('```', '').strip()
        replies = json.loads(text)
        if not isinstance(replies, list):
            replies = []
        # Filter: max 5 words, max 4 items
        replies = [r for r in replies if isinstance(r, str) and len(r.split()) <= 6][:4]
        return web.Response(text=json.dumps({'replies': replies}), content_type='application/json')

    except Exception as e:
        print(f'[smart_replies] error: {e}')
        return web.Response(text=json.dumps({'replies': []}), content_type='application/json')

async def main():
    port = int(os.environ.get('PORT', 8080))
    app  = web.Application(client_max_size=50*1024*1024)
    app.router.add_get('/',              index_handler)
    app.router.add_get('/ws',            ws_handler)
    app.router.add_post('/upload',       upload_handler)
    app.router.add_get('/media/{fid}',   media_handler)
    app.router.add_get('/manifest.json', manifest_handler)
    app.router.add_get('/vapid-key',      vapid_handler)
    app.router.add_get('/sw.js',          sw_handler)
    app.router.add_get('/logo',           logo_handler)
    app.router.add_get('/icon.png',       icon_png_handler)
    app.router.add_post('/translate',    translate_handler)
    app.router.add_post('/smart-replies', smart_replies_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f'[*] Supend PWA на порту {port}')
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
