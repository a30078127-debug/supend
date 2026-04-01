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
    m = {"name":"Supend","short_name":"Supend","start_url":"/","display":"standalone",
         "background_color":"#ffffff","theme_color":"#1ABC9C",
         "icons":[{"src":"/logo","sizes":"192x192","type":"image/jpeg"},
                  {"src":"/logo","sizes":"512x512","type":"image/jpeg"}]}
    return web.Response(text=json.dumps(m), content_type='application/json')

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
    # Отдаём логотип из файла logo.jpg если он есть
    logo_path = 'logo.jpg'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            data = f.read()
        return web.Response(body=data, content_type='image/jpeg',
                          headers={'Cache-Control':'public,max-age=86400'})
    # Fallback — SVG логотип
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect width="192" height="192" rx="40" fill="#1ABC9C"/><text x="96" y="130" font-size="100" text-anchor="middle" fill="white" font-family="Arial">S</text></svg>'
    return web.Response(body=svg, content_type='image/svg+xml')

async def translate_handler(request):
    try:
        body = await request.json()
        text = body.get('text', '').strip()
        lang = body.get('lang', 'en')
        if not text:
            return web.Response(text=json.dumps({'result': ''}), content_type='application/json')

        # Бесплатный Google Translate (без ключа)
        import urllib.parse
        encoded = urllib.parse.quote(text)
        url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang}&dt=t&q={encoded}'

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            # Структура: [[[переведённый текст, оригинал, ...], ...], ...]
            translated = ''.join(
                part[0] for part in data[0] if part and part[0]
            )
        return web.Response(text=json.dumps({'result': translated}), content_type='application/json')
    except Exception as e:
        print(f'[translate] error: {e}')
        return web.Response(text=json.dumps({'result': f'Ошибка перевода: {str(e)}'}), content_type='application/json')

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
    app.router.add_post('/translate',    translate_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f'[*] Supend PWA на порту {port}')
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
