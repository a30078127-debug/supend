"""Сетевой слой P2P мессенджера."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass

import nacl.public
import nacl.exceptions

from core.crypto import CryptoCore, SessionKeys
from core.protocol import Protocol, Message, MessageType, ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class PeerInfo:
    peer_id: str
    host: str
    port: int
    connected_at: float = 0.0
    last_seen: float = 0.0


class PeerConnection:
    PING_INTERVAL = 30
    PING_TIMEOUT  = 10
    HANDSHAKE_TIMEOUT = 15

    def __init__(self, crypto, reader, writer, is_initiator, on_message, on_disconnect):
        self.crypto = crypto
        self.reader = reader
        self.writer = writer
        self.is_initiator = is_initiator
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.peer_info = None
        self.session = None
        self._connected = False
        self._ping_task = None
        self._our_ephemeral_private = None
        self._our_ephemeral_public = None

    @property
    def peer_id(self):
        return self.peer_info.peer_id if self.peer_info else None

    @property
    def is_connected(self):
        return self._connected

    async def start(self):
        try:
            success = await asyncio.wait_for(self._perform_handshake(), timeout=self.HANDSHAKE_TIMEOUT)
            if not success:
                return False
            self._connected = True
            self._ping_task = asyncio.create_task(self._ping_loop())
            asyncio.create_task(self._receive_loop())
            return True
        except asyncio.TimeoutError:
            return False
        except Exception as e:
            logger.error("Ошибка запуска соединения: %s", e)
            return False

    async def _perform_handshake(self):
        self._our_ephemeral_private, self._our_ephemeral_public = self.crypto.generate_ephemeral_keypair()
        payload = self.crypto.create_handshake_payload(self._our_ephemeral_public)
        if self.is_initiator:
            return await self._handshake_as_initiator(payload)
        else:
            return await self._handshake_as_responder(payload)

    async def _handshake_as_initiator(self, our_payload):
        await self._send_raw(Protocol.handshake_init(our_payload))
        msg = await self._recv_message()
        if msg is None or msg.type != MessageType.HANDSHAKE_ACK:
            return False
        ok, their_identity, their_ephemeral = self.crypto.verify_handshake_payload(msg.payload)
        if not ok:
            return False
        their_pub = nacl.public.PublicKey(their_ephemeral)
        self.session = self.crypto.compute_session_keys(self._our_ephemeral_private, their_pub, we_are_initiator=True)
        host, port = self.writer.get_extra_info('peername', ('?', 0))
        self.peer_info = PeerInfo(peer_id=their_identity.hex(), host=host, port=port, connected_at=time.time(), last_seen=time.time())
        await self._send_raw(Protocol.handshake_done())
        self._cleanup_ephemeral()
        logger.info("Handshake завершён с %s", self.peer_info.peer_id[:16])
        return True

    async def _handshake_as_responder(self, our_payload):
        msg = await self._recv_message()
        if msg is None or msg.type != MessageType.HANDSHAKE_INIT:
            return False
        ok, their_identity, their_ephemeral = self.crypto.verify_handshake_payload(msg.payload)
        if not ok:
            return False
        their_pub = nacl.public.PublicKey(their_ephemeral)
        self.session = self.crypto.compute_session_keys(self._our_ephemeral_private, their_pub, we_are_initiator=False)
        host, port = self.writer.get_extra_info('peername', ('?', 0))
        self.peer_info = PeerInfo(peer_id=their_identity.hex(), host=host, port=port, connected_at=time.time(), last_seen=time.time())
        await self._send_raw(Protocol.handshake_ack(our_payload))
        msg = await self._recv_message()
        if msg is None or msg.type != MessageType.HANDSHAKE_DONE:
            return False
        self._cleanup_ephemeral()
        logger.info("Handshake завершён с %s", self.peer_info.peer_id[:16])
        return True

    def _cleanup_ephemeral(self):
        self._our_ephemeral_private = None
        self._our_ephemeral_public = None

    async def send_chat(self, text):
        if not self._connected or not self.session:
            raise RuntimeError("Нет активного соединения")
        chat = ChatMessage(sender_id=self.crypto.peer_id, text=text)
        encrypted = self.crypto.encrypt(self.session, chat.to_bytes())
        await self._send_raw(Protocol.chat_message(encrypted))

    async def _receive_loop(self):
        try:
            while self._connected:
                msg = await self._recv_message()
                if msg is None:
                    break
                await self._handle_message(msg)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Ошибка receive_loop: %s", e)
        finally:
            await self._handle_disconnect()

    async def _handle_message(self, msg):
        if self.peer_info:
            self.peer_info.last_seen = time.time()
        if msg.type == MessageType.CHAT_MESSAGE:
            if not self.session:
                return
            try:
                encrypted_data = bytes.fromhex(msg.payload["d"])
                plaintext = self.crypto.decrypt(self.session, encrypted_data)
                chat_msg = ChatMessage.from_bytes(plaintext)
                await self.on_message(self.peer_id, chat_msg)
            except (nacl.exceptions.CryptoError, ValueError) as e:
                logger.error("Ошибка расшифровки: %s", e)
        elif msg.type == MessageType.PING:
            await self._send_raw(Protocol.pong())
        elif msg.type == MessageType.DISCONNECT:
            self._connected = False

    async def disconnect(self, reason="bye"):
        if self._connected:
            try:
                await self._send_raw(Protocol.disconnect(reason))
            except Exception:
                pass
        self._connected = False
        if self._ping_task:
            self._ping_task.cancel()
        if self.session:
            self.session.destroy()
            self.session = None
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass

    async def _handle_disconnect(self):
        self._connected = False
        if self.session:
            self.session.destroy()
            self.session = None
        if self._ping_task:
            self._ping_task.cancel()
        if self.peer_id:
            await self.on_disconnect(self.peer_id)

    async def _ping_loop(self):
        try:
            while self._connected:
                await asyncio.sleep(self.PING_INTERVAL)
                if not self._connected:
                    break
                try:
                    await asyncio.wait_for(self._send_raw(Protocol.ping()), timeout=self.PING_TIMEOUT)
                except asyncio.TimeoutError:
                    await self._handle_disconnect()
                    break
        except asyncio.CancelledError:
            pass

    async def _send_raw(self, data):
        self.writer.write(data)
        await self.writer.drain()

    async def _recv_message(self):
        try:
            header = await asyncio.wait_for(self.reader.readexactly(4), timeout=60)
            length = Protocol.parse_frame_length(header)
            body = await asyncio.wait_for(self.reader.readexactly(length), timeout=30)
            return Message.from_bytes(body)
        except asyncio.IncompleteReadError:
            return None
        except asyncio.TimeoutError:
            return None
        except (ValueError, json.JSONDecodeError):
            return None


class P2PNode:
    def __init__(self, crypto, host="0.0.0.0", port=0):
        self.crypto = crypto
        self.host = host
        self.port = port
        self._server = None
        self._peers = {}
        self._message_handlers = []
        self._connect_handlers = []
        self._disconnect_handlers = []

    @property
    def peer_id(self):
        return self.crypto.peer_id

    @property
    def peers(self):
        return dict(self._peers)

    def on_message(self, handler):
        self._message_handlers.append(handler)

    def on_connect(self, handler):
        self._connect_handlers.append(handler)

    def on_disconnect(self, handler):
        self._disconnect_handlers.append(handler)

    async def start(self):
        self._server = await asyncio.start_server(self._handle_incoming, self.host, self.port)
        self.port = self._server.sockets[0].getsockname()[1]
        return self.port

    async def stop(self):
        for conn in list(self._peers.values()):
            await conn.disconnect("shutdown")
        self._peers.clear()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def connect_to(self, host, port):
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=10)
        except Exception as e:
            logger.warning("Не удалось подключиться к %s:%d: %s", host, port, e)
            return False
        conn = PeerConnection(
            crypto=self.crypto, reader=reader, writer=writer,
            is_initiator=True, on_message=self._dispatch_message,
            on_disconnect=self._handle_peer_disconnect,
        )
        success = await conn.start()
        if success and conn.peer_id:
            self._peers[conn.peer_id] = conn
            for handler in self._connect_handlers:
                asyncio.create_task(handler(conn.peer_info))
        else:
            await conn.disconnect()
        return success

    async def send_to(self, peer_id, text):
        conn = self._peers.get(peer_id)
        if not conn or not conn.is_connected:
            return False
        try:
            await conn.send_chat(text)
            return True
        except Exception as e:
            logger.error("Ошибка отправки: %s", e)
            return False

    async def disconnect_peer(self, peer_id):
        conn = self._peers.pop(peer_id, None)
        if conn:
            await conn.disconnect()

    async def _handle_incoming(self, reader, writer):
        conn = PeerConnection(
            crypto=self.crypto, reader=reader, writer=writer,
            is_initiator=False, on_message=self._dispatch_message,
            on_disconnect=self._handle_peer_disconnect,
        )
        success = await conn.start()
        if success and conn.peer_id:
            self._peers[conn.peer_id] = conn
            for handler in self._connect_handlers:
                asyncio.create_task(handler(conn.peer_info))

    async def _dispatch_message(self, peer_id, msg):
        for handler in self._message_handlers:
            asyncio.create_task(handler(peer_id, msg))

    async def _handle_peer_disconnect(self, peer_id):
        self._peers.pop(peer_id, None)
        for handler in self._disconnect_handlers:
            asyncio.create_task(handler(peer_id))
