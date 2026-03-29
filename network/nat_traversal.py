"""NAT Traversal через UDP Hole Punching."""

import asyncio
import json
import logging
import socket
import struct
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class UDPHolePuncher:
    PUNCH_ATTEMPTS = 10
    PUNCH_INTERVAL = 0.5

    def __init__(self, local_port=0):
        self.local_port = local_port

    async def get_public_address(self, stun_host="stun.l.google.com"):
        try:
            return await asyncio.wait_for(self._stun_request(stun_host, 3478), timeout=5)
        except Exception as e:
            logger.warning("STUN не удался: %s", e)
            return None

    async def _stun_request(self, host, port):
        transaction_id = b'\x01' * 12
        stun_msg = b'\x00\x01\x00\x00\x21\x12\xa4\x42' + transaction_id
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind(('', self.local_port))
        if self.local_port == 0:
            self.local_port = sock.getsockname()[1]
        try:
            await loop.sock_sendto(sock, stun_msg, (host, port))
            response = await asyncio.wait_for(loop.sock_recv(sock, 1024), timeout=3)
            return self._parse_stun_response(response)
        finally:
            sock.close()

    def _parse_stun_response(self, data):
        if len(data) < 20:
            return None
        msg_type = struct.unpack('>H', data[0:2])[0]
        if msg_type != 0x0101:
            return None
        offset = 20
        while offset < len(data):
            if offset + 4 > len(data):
                break
            attr_type = struct.unpack('>H', data[offset:offset+2])[0]
            attr_len  = struct.unpack('>H', data[offset+2:offset+4])[0]
            attr_val  = data[offset+4:offset+4+attr_len]
            if attr_type == 0x0020 and len(attr_val) >= 8:
                magic = 0x2112A442
                port = struct.unpack('>H', attr_val[2:4])[0] ^ (magic >> 16)
                ip_int = struct.unpack('>I', attr_val[4:8])[0] ^ magic
                ip = socket.inet_ntoa(struct.pack('>I', ip_int))
                return ip, port
            if attr_type == 0x0001 and len(attr_val) >= 8:
                port = struct.unpack('>H', attr_val[2:4])[0]
                ip = socket.inet_ntoa(attr_val[4:8])
                return ip, port
            offset += 4 + attr_len + (4 - attr_len % 4) % 4
        return None

    async def punch(self, their_host, their_port, our_peer_id):
        punch_packet = json.dumps({"type": "punch", "from": our_peer_id}).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind(('', self.local_port))
        loop = asyncio.get_event_loop()
        received = asyncio.Event()

        async def recv_loop():
            while not received.is_set():
                try:
                    data = await asyncio.wait_for(loop.sock_recv(sock, 1024), timeout=1)
                    msg = json.loads(data.decode())
                    if msg.get("type") == "punch":
                        received.set()
                except Exception:
                    pass

        task = asyncio.create_task(recv_loop())
        try:
            for _ in range(self.PUNCH_ATTEMPTS):
                await loop.sock_sendto(sock, punch_packet, (their_host, their_port))
                await asyncio.sleep(self.PUNCH_INTERVAL)
                if received.is_set():
                    break
            return received.is_set()
        finally:
            task.cancel()
            sock.close()
