"""Supend Web Server — простой мессенджер для браузера."""
import asyncio, json, os, hashlib, time, uuid
from aiohttp import web

# ── База данных в памяти ──────────────────────────────────────────────────────
users = {}      # username -> {password_hash, bio, avatar, created_at}
sessions = {}   # token -> username
online = {}     # username -> ws
messages = {}   # chat_id -> [{id, from, text, time, type}]
calls = {}      # call_id -> {from, to, type, status}

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def chat_id(a, b): return '_'.join(sorted([a, b]))
def ts(): return int(time.time() * 1000)

# ── WebSocket handler ─────────────────────────────────────────────────────────
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    current_user = None
    
    async def send(data):
        try: await ws.send_str(json.dumps(data))
        except: pass

    async def broadcast_to(username, data):
        if username in online:
            try: await online[username].send_str(json.dumps(data))
            except: pass

    async for msg in ws:
        if msg.type != web.WSMsgType.TEXT:
            break
        try:
            data = json.loads(msg.data)
            cmd = data.get('cmd')

            # ── Регистрация ───────────────────────────────────────────────────
            if cmd == 'register':
                u = data['username'].strip().lower()
                p = data['password']
                if not u or not p:
                    await send({'type': 'error', 'msg': 'Введи логин и пароль'}); continue
                if len(u) < 3:
                    await send({'type': 'error', 'msg': 'Логин минимум 3 символа'}); continue
                if not u.replace('_','').isalnum():
                    await send({'type': 'error', 'msg': 'Только буквы, цифры и _'}); continue
                if u in users:
                    await send({'type': 'register_error', 'msg': 'Логин занят'}); continue
                users[u] = {
                    'password': hash_password(p),
                    'bio': data.get('bio', ''),
                    'avatar': data.get('avatar', ''),
                    'created_at': ts()
                }
                token = str(uuid.uuid4())
                sessions[token] = u
                current_user = u
                online[u] = ws
                await send({'type': 'auth_ok', 'username': u, 'token': token,
                           'bio': users[u]['bio'], 'avatar': users[u]['avatar']})

            # ── Вход ─────────────────────────────────────────────────────────
            elif cmd == 'login':
                u = data['username'].strip().lower()
                p = data['password']
                if u not in users:
                    await send({'type': 'login_error', 'msg': 'Пользователь не найден'}); continue
                if users[u]['password'] != hash_password(p):
                    await send({'type': 'login_error', 'msg': 'Неверный пароль'}); continue
                token = str(uuid.uuid4())
                sessions[token] = u
                current_user = u
                online[u] = ws
                await send({'type': 'auth_ok', 'username': u, 'token': token,
                           'bio': users[u]['bio'], 'avatar': users[u]['avatar']})
                # Уведомить контакты что онлайн
                for cid, msgs in messages.items():
                    if u in cid.split('_'):
                        other = [x for x in cid.split('_') if x != u]
                        if other and other[0] in online:
                            await broadcast_to(other[0], {'type': 'user_online', 'username': u})

            # ── Поиск пользователя ────────────────────────────────────────────
            elif cmd == 'search':
                if not current_user:
                    await send({'type': 'error', 'msg': 'Не авторизован'}); continue
                q = data.get('username', '').strip().lower()
                if q in users and q != current_user:
                    u_data = users[q]
                    await send({'type': 'search_result', 'found': True,
                               'username': q, 'bio': u_data.get('bio', ''),
                               'avatar': u_data.get('avatar', ''),
                               'online': q in online})
                else:
                    await send({'type': 'search_result', 'found': False})

            # ── Отправка сообщения ────────────────────────────────────────────
            elif cmd == 'send_msg':
                if not current_user: continue
                to = data['to']
                text = data.get('text', '').strip()
                if not text or to not in users: continue
                cid = chat_id(current_user, to)
                if cid not in messages: messages[cid] = []
                msg_obj = {
                    'id': str(uuid.uuid4()),
                    'from': current_user,
                    'to': to,
                    'text': text,
                    'time': ts(),
                    'type': 'text',
                    'reply_to': data.get('reply_to'),
                }
                messages[cid].append(msg_obj)
                # Отправить отправителю
                await send({'type': 'message', **msg_obj})
                # Отправить получателю если онлайн
                if to in online:
                    await broadcast_to(to, {'type': 'message', **msg_obj})

            # ── Загрузка истории ──────────────────────────────────────────────
            elif cmd == 'get_history':
                if not current_user: continue
                with_user = data.get('with')
                if not with_user: continue
                cid = chat_id(current_user, with_user)
                msgs = messages.get(cid, [])[-100:]  # последние 100
                await send({'type': 'history', 'with': with_user, 'messages': msgs})

            # ── WebRTC сигналинг ──────────────────────────────────────────────
            elif cmd == 'call_signal':
                if not current_user: continue
                to = data.get('to')
                if to and to in online:
                    await broadcast_to(to, {
                        'type': 'call_signal',
                        'from': current_user,
                        'signal': data.get('signal'),
                        'call_type': data.get('call_type', 'voice')
                    })

            # ── Статус звонка ─────────────────────────────────────────────────
            elif cmd == 'call_status':
                if not current_user: continue
                to = data.get('to')
                if to and to in online:
                    await broadcast_to(to, {
                        'type': 'call_status',
                        'from': current_user,
                        'status': data.get('status')
                    })

            # ── Получить список чатов ─────────────────────────────────────────
            elif cmd == 'get_chats':
                if not current_user: continue
                chats = []
                for cid, msgs in messages.items():
                    if current_user in cid.split('_') and msgs:
                        other = [x for x in cid.split('_') if x != current_user][0]
                        last = msgs[-1]
                        unread = sum(1 for m in msgs if m['from'] != current_user and not m.get('read'))
                        chats.append({
                            'username': other,
                            'last_msg': last['text'],
                            'last_time': last['time'],
                            'unread': unread,
                            'online': other in online,
                            'avatar': users.get(other, {}).get('avatar', ''),
                            'bio': users.get(other, {}).get('bio', ''),
                        })
                chats.sort(key=lambda x: x['last_time'], reverse=True)
                await send({'type': 'chats', 'chats': chats})

            # ── Прочитать сообщения ───────────────────────────────────────────
            elif cmd == 'mark_read':
                if not current_user: continue
                with_user = data.get('with')
                cid = chat_id(current_user, with_user)
                for m in messages.get(cid, []):
                    if m['from'] != current_user:
                        m['read'] = True

        except Exception as e:
            print(f'WS error: {e}')

    # Отключение
    if current_user:
        online.pop(current_user, None)
        # Уведомить контакты
        for cid in messages:
            if current_user in cid.split('_'):
                other = [x for x in cid.split('_') if x != current_user]
                if other and other[0] in online:
                    await broadcast_to(other[0], {'type': 'user_offline', 'username': current_user})
    return ws

# ── HTTP handler (отдаёт HTML) ────────────────────────────────────────────────
async def index_handler(request):
    html = open('index.html', encoding='utf-8').read()
    return web.Response(text=html, content_type='text/html')

async def manifest_handler(request):
    m = {
        "name": "Supend",
        "short_name": "Supend",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#1ABC9C",
        "icons": [
            {"src": "/icon.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    return web.Response(text=json.dumps(m), content_type='application/json')

# ── Запуск ────────────────────────────────────────────────────────────────────
async def main():
    port = int(os.environ.get('PORT', 8080))
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/ws', ws_handler)
    app.router.add_get('/manifest.json', manifest_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f'[*] Supend запущен на порту {port}')
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
