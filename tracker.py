"""Трекер с поддержкой логинов, маркетплейса, relay и сигналинга звонков."""

import asyncio
import json
import logging
import time
import struct

logger = logging.getLogger(__name__)


class TrackerServer:
    PEER_TTL = 300

    def __init__(self, host="0.0.0.0", port=9000):
        self.host = host
        self.port = port
        self._peers = {}
        self._usernames = {}
        self._market = {}
        self._relay_queues = {}   # peer_id -> list of (from_id, payload)
        self._signal_queues = {}  # peer_id -> list of {from, data}
        self._server = None

    async def start(self):
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        asyncio.create_task(self._cleanup_loop())
        logger.info("Трекер запущен на %s:%d", self.host, self.port)
        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        client_ip = addr[0] if addr else "unknown"
        try:
            while True:
                header = await asyncio.wait_for(reader.readexactly(4), timeout=60)
                length = struct.unpack('>I', header)[0]
                if length > 2097152:
                    break
                body = await asyncio.wait_for(reader.readexactly(length), timeout=15)
                msg = json.loads(body.decode('utf-8'))
                msg_type = msg.get("t")

                # Регистрация
                if msg_type == 40:
                    peer_id = msg["p"]["id"]
                    peer_port = msg["p"]["port"]
                    username = msg["p"].get("username", "").strip().lower()
                    self._peers[peer_id] = {
                        "ip": client_ip, "port": peer_port,
                        "username": username, "ts": time.time()
                    }
                    if username:
                        self._usernames[username] = peer_id
                    resp = json.dumps({"t": 42, "p": {"ok": True}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Поиск по username
                elif msg_type == 43:
                    username = msg["p"].get("username", "").strip().lower()
                    peer_id = self._usernames.get(username)
                    if peer_id and peer_id in self._peers:
                        info = self._peers[peer_id]
                        resp = json.dumps({"t": 42, "p": {
                            "found": True, "ip": info["ip"],
                            "port": info["port"], "username": username,
                            "peer_id": peer_id,
                        }}).encode()
                    else:
                        resp = json.dumps({"t": 42, "p": {"found": False}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Поиск по peer_id
                elif msg_type == 41:
                    peer_id = msg["p"]["id"]
                    peers = []
                    if peer_id == "*":
                        for pid, info in self._peers.items():
                            if info["ip"] != client_ip:
                                peers.append({"id": pid, "ip": info["ip"], "port": info["port"]})
                    elif peer_id in self._peers:
                        info = self._peers[peer_id]
                        peers.append({"id": peer_id, "ip": info["ip"], "port": info["port"]})
                    resp = json.dumps({"t": 42, "p": {"peers": peers}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Relay: отправить сообщение (тип 44)
                elif msg_type == 44:
                    from_id = msg["p"]["from"]
                    to_id = msg["p"]["to"]
                    payload = msg["p"]["data"]
                    if to_id not in self._relay_queues:
                        self._relay_queues[to_id] = []
                    self._relay_queues[to_id].append((from_id, payload))
                    resp = json.dumps({"t": 42, "p": {"ok": True}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Relay: получить сообщения (тип 45)
                elif msg_type == 45:
                    peer_id = msg["p"]["id"]
                    msgs = self._relay_queues.pop(peer_id, [])
                    resp = json.dumps({"t": 42, "p": {
                        "messages": [{"from": f, "data": d} for f, d in msgs]
                    }}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Сигналинг звонка: отправить (тип 46)
                elif msg_type == 46:
                    from_id = msg["p"]["from"]
                    to_id = msg["p"]["to"]
                    data = msg["p"]["data"]
                    if to_id not in self._signal_queues:
                        self._signal_queues[to_id] = []
                    self._signal_queues[to_id].append({"from": from_id, "data": data})
                    resp = json.dumps({"t": 42, "p": {"ok": True}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Сигналинг звонка: получить (тип 47)
                elif msg_type == 47:
                    peer_id = msg["p"]["id"]
                    signals = self._signal_queues.pop(peer_id, [])
                    resp = json.dumps({"t": 42, "p": {"signals": signals}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Маркетплейс: опубликовать
                elif msg_type == 50:
                    theme = msg["p"].get("theme", {})
                    theme_id = theme.get("id")
                    if theme_id:
                        self._market[theme_id] = theme
                    resp = json.dumps({"t": 42, "p": {"ok": True}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Маркетплейс: получить
                elif msg_type == 51:
                    themes = list(self._market.values())
                    resp = json.dumps({"t": 42, "p": {"themes": themes}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            now = time.time()
            expired = [pid for pid, info in self._peers.items() if now - info["ts"] > self.PEER_TTL]
            for pid in expired:
                info = self._peers.pop(pid)
                uname = info.get("username", "")
                if uname and self._usernames.get(uname) == pid:
                    del self._usernames[uname]
            self._relay_queues = {k: v for k, v in self._relay_queues.items() if v}
            self._signal_queues = {k: v for k, v in self._signal_queues.items() if v}


class TrackerClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def _connect(self, timeout=10):
        return await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=timeout)

    async def register(self, peer_id, listen_port, username=""):
        try:
            reader, writer = await self._connect()
            msg = json.dumps({
                "t": 40,
                "p": {"id": peer_id, "port": listen_port, "username": username}
            }).encode()
            writer.write(struct.pack('>I', len(msg)) + msg)
            await writer.drain()
            header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
            length = struct.unpack('>I', header)[0]
            body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
            resp = json.loads(body.decode())
            writer.close()
            return resp.get("p", {}).get("ok", False)
        except Exception as e:
            logger.warning("Ошибка регистрации: %s", e)
            return False

    async def lookup_by_username(self, username):
        try:
            reader, writer = await self._connect()
            msg = json.dumps({"t": 43, "p": {"username": username}}).encode()
            writer.write(struct.pack('>I', len(msg)) + msg)
            await writer.drain()
            header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
            length = struct.unpack('>I', header)[0]
            body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
            resp = json.loads(body.decode())
            writer.close()
            p = resp.get("p", {})
            if p.get("found"):
                return {"ip": p["ip"], "port": p["port"], "peer_id": p.get("peer_id")}
            return None
        except Exception as e:
            logger.warning("Ошибка поиска: %s", e)
            return None

    async def lookup(self, peer_id="*"):
        try:
            reader, writer = await self._connect()
            msg = json.dumps({"t": 41, "p": {"id": peer_id}}).encode()
            writer.write(struct.pack('>I', len(msg)) + msg)
            await writer.drain()
            header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
            length = struct.unpack('>I', header)[0]
            body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
            resp = json.loads(body.decode())
            writer.close()
            return resp.get("p", {}).get("peers", [])
        except Exception as e:
            logger.warning("Ошибка поиска: %s", e)
            return []

    async def send_relay(self, from_id, to_id, payload):
        try:
            reader, writer = await self._connect()
            msg = json.dumps({"t": 44, "p": {"from": from_id, "to": to_id, "data": payload}}).encode()
            writer.write(struct.pack('>I', len(msg)) + msg)
            await writer.drain()
            header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
            length = struct.unpack('>I', header)[0]
            await asyncio.wait_for(reader.readexactly(length), timeout=10)
            writer.close()
            return True
        except Exception as e:
            logger.warning("send_relay error: %s", e)
            return False

    async def start_relay_listener(self, peer_id, callback):
        async def _poll():
            while True:
                await asyncio.sleep(2)
                try:
                    reader, writer = await self._connect()
                    msg = json.dumps({"t": 45, "p": {"id": peer_id}}).encode()
                    writer.write(struct.pack('>I', len(msg)) + msg)
                    await writer.drain()
                    header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
                    length = struct.unpack('>I', header)[0]
                    body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
                    resp = json.loads(body.decode())
                    writer.close()
                    for m in resp.get("p", {}).get("messages", []):
                        await callback(m["from"], m["data"])
                except Exception:
                    pass
        asyncio.create_task(_poll())

    async def send_signal(self, from_id, to_id, data):
        """Отправить WebRTC сигнал через трекер."""
        try:
            reader, writer = await self._connect()
            msg = json.dumps({"t": 46, "p": {"from": from_id, "to": to_id, "data": data}}).encode()
            writer.write(struct.pack('>I', len(msg)) + msg)
            await writer.drain()
            header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
            length = struct.unpack('>I', header)[0]
            await asyncio.wait_for(reader.readexactly(length), timeout=10)
            writer.close()
            return True
        except Exception as e:
            logger.warning("send_signal error: %s", e)
            return False

    async def start_signal_listener(self, peer_id, callback):
        """Слушать входящие WebRTC сигналы через трекер."""
        async def _poll():
            while True:
                await asyncio.sleep(1)
                try:
                    reader, writer = await self._connect()
                    msg = json.dumps({"t": 47, "p": {"id": peer_id}}).encode()
                    writer.write(struct.pack('>I', len(msg)) + msg)
                    await writer.drain()
                    header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
                    length = struct.unpack('>I', header)[0]
                    body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
                    resp = json.loads(body.decode())
                    writer.close()
                    for s in resp.get("p", {}).get("signals", []):
                        await callback(s["from"], s["data"])
                except Exception:
                    pass
        asyncio.create_task(_poll())

    async def publish_theme(self, theme):
        try:
            reader, writer = await self._connect()
            msg = json.dumps({"t": 50, "p": {"theme": theme}}).encode()
            writer.write(struct.pack('>I', len(msg)) + msg)
            await writer.drain()
            header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
            length = struct.unpack('>I', header)[0]
            body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
            resp = json.loads(body.decode())
            writer.close()
            return resp.get("p", {}).get("ok", False)
        except Exception as e:
            logger.warning("Ошибка публикации: %s", e)
            return False

    async def get_market_themes(self):
        try:
            reader, writer = await self._connect()
            msg = json.dumps({"t": 51, "p": {}}).encode()
            writer.write(struct.pack('>I', len(msg)) + msg)
            await writer.drain()
            header = await asyncio.wait_for(reader.readexactly(4), timeout=10)
            length = struct.unpack('>I', header)[0]
            body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
            resp = json.loads(body.decode())
            writer.close()
            return resp.get("p", {}).get("themes", [])
        except Exception as e:
            logger.warning("Ошибка маркетплейса: %s", e)
            return []
