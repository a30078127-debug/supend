"""Протокол сообщений P2P мессенджера."""

import json
import time
import struct
import logging
from enum import IntEnum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class MessageType(IntEnum):
    HANDSHAKE_INIT   = 1
    HANDSHAKE_ACK    = 2
    HANDSHAKE_DONE   = 3
    CHAT_MESSAGE     = 10
    PING             = 20
    PONG             = 21
    DISCONNECT       = 30
    TRACKER_REGISTER = 40
    TRACKER_LOOKUP   = 41
    TRACKER_RESPONSE = 42


@dataclass
class Message:
    type: int
    payload: dict
    timestamp: int = field(default_factory=lambda: int(time.time()))

    def to_bytes(self):
        data = {"t": self.type, "ts": self.timestamp, "p": self.payload}
        return json.dumps(data, separators=(',', ':')).encode('utf-8')

    @classmethod
    def from_bytes(cls, data):
        obj = json.loads(data.decode('utf-8'))
        return cls(type=obj["t"], timestamp=obj.get("ts", 0), payload=obj.get("p", {}))


class Protocol:
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024

    @staticmethod
    def handshake_init(payload):
        return Protocol._frame(Message(type=MessageType.HANDSHAKE_INIT, payload=payload).to_bytes())

    @staticmethod
    def handshake_ack(payload):
        return Protocol._frame(Message(type=MessageType.HANDSHAKE_ACK, payload=payload).to_bytes())

    @staticmethod
    def handshake_done():
        return Protocol._frame(Message(type=MessageType.HANDSHAKE_DONE, payload={}).to_bytes())

    @staticmethod
    def chat_message(encrypted_data):
        msg = Message(type=MessageType.CHAT_MESSAGE, payload={"d": encrypted_data.hex()})
        return Protocol._frame(msg.to_bytes())

    @staticmethod
    def ping():
        return Protocol._frame(Message(type=MessageType.PING, payload={}).to_bytes())

    @staticmethod
    def pong():
        return Protocol._frame(Message(type=MessageType.PONG, payload={}).to_bytes())

    @staticmethod
    def disconnect(reason=""):
        return Protocol._frame(Message(type=MessageType.DISCONNECT, payload={"reason": reason}).to_bytes())

    @staticmethod
    def tracker_register(peer_id, port):
        return Protocol._frame(Message(type=MessageType.TRACKER_REGISTER, payload={"id": peer_id, "port": port}).to_bytes())

    @staticmethod
    def tracker_lookup(peer_id):
        return Protocol._frame(Message(type=MessageType.TRACKER_LOOKUP, payload={"id": peer_id}).to_bytes())

    @staticmethod
    def tracker_response(peers):
        return Protocol._frame(Message(type=MessageType.TRACKER_RESPONSE, payload={"peers": peers}).to_bytes())

    @staticmethod
    def _frame(data):
        length = len(data)
        if length > Protocol.MAX_MESSAGE_SIZE:
            raise ValueError(f"Сообщение слишком большое: {length}")
        return struct.pack('>I', length) + data

    @staticmethod
    def parse_frame_length(header):
        if len(header) < 4:
            raise ValueError("Недостаточно данных")
        length = struct.unpack('>I', header[:4])[0]
        if length > Protocol.MAX_MESSAGE_SIZE:
            raise ValueError(f"Подозрительно большой фрейм: {length}")
        return length


class ChatMessage:
    def __init__(self, sender_id, text, timestamp=None):
        self.sender_id = sender_id
        self.text = text
        self.timestamp = timestamp or int(time.time())

    def to_bytes(self):
        return json.dumps({"from": self.sender_id, "text": self.text, "ts": self.timestamp}, ensure_ascii=False).encode('utf-8')

    @classmethod
    def from_bytes(cls, data):
        obj = json.loads(data.decode('utf-8'))
        return cls(sender_id=obj["from"], text=obj["text"], timestamp=obj.get("ts", 0))
