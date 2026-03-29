"""Трекер с поддержкой логинов для поиска по имени."""

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
        self._peers = {}       # peer_id -> {ip, port, username, ts}
        self._usernames = {}   # username -> peer_id
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
                header = await asyncio.wait_for(reader.readexactly(4), timeout=30)
                length = struct.unpack('>I', header)[0]
                if length > 65536:
                    break
                body = await asyncio.wait_for(reader.readexactly(length), timeout=10)
                msg = json.loads(body.decode('utf-8'))
                msg_type = msg.get("t")

                # Регистрация (с логином)
                if msg_type == 40:
                    peer_id  = msg["p"]["id"]
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

                # Поиск по логину (новый тип 43)
                elif msg_type == 43:
                    username = msg["p"].get("username", "").strip().lower()
                    peer_id = self._usernames.get(username)
                    if peer_id and peer_id in self._peers:
                        info = self._peers[peer_id]
                        resp = json.dumps({"t": 42, "p": {
                            "found": True,
                            "ip": info["ip"],
                            "port": info["port"],
                            "username": username,
                        }}).encode()
                    else:
                        resp = json.dumps({"t": 42, "p": {"found": False}}).encode()
                    writer.write(struct.pack('>I', len(resp)) + resp)
                    await writer.drain()

                # Поиск по peer_id (старый тип 41)
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


class TrackerClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def register(self, peer_id, listen_port, username=""):
        """Регистрация с логином."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=10)
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
        """Найти пира по логину."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=10)
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
                return {"ip": p["ip"], "port": p["port"]}
            return None
        except Exception as e:
            logger.warning("Ошибка поиска по логину: %s", e)
            return None

    async def lookup(self, peer_id="*"):
        """Поиск по peer_id (старый метод)."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=10)
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
