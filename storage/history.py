"""Зашифрованное локальное хранилище истории чатов."""

import json
import logging
import time
from pathlib import Path

import nacl.secret
import nacl.exceptions

logger = logging.getLogger(__name__)


class ChatHistory:
    def __init__(self, peer_id, text, is_outgoing, timestamp):
        self.peer_id = peer_id
        self.text = text
        self.is_outgoing = is_outgoing
        self.timestamp = timestamp

    def to_dict(self):
        return {"pid": self.peer_id, "txt": self.text, "out": self.is_outgoing, "ts": self.timestamp}

    @classmethod
    def from_dict(cls, d):
        return cls(peer_id=d["pid"], text=d["txt"], is_outgoing=d["out"], timestamp=d["ts"])


class EncryptedStorage:
    def __init__(self, crypto, base_dir=None):
        self.crypto = crypto
        self.base_dir = base_dir or Path.home() / ".p2p_messenger"
        self.history_dir = self.base_dir / "history"
        self._box = None
        self._cache = {}
        self.history_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.history_dir.chmod(0o700)
        except Exception:
            pass

    def unlock(self, password):
        self._box = self.crypto.derive_storage_key(password)

    def lock(self):
        self._box = None
        self._cache.clear()

    @property
    def is_unlocked(self):
        return self._box is not None

    def save_message(self, peer_id, text, is_outgoing):
        if not self._box:
            return
        entry = ChatHistory(peer_id=peer_id, text=text, is_outgoing=is_outgoing, timestamp=int(time.time()))
        history = self._load_history(peer_id)
        history.append(entry)
        if len(history) > 1000:
            history = history[-1000:]
        self._save_history(peer_id, history)

    def load_history(self, peer_id, limit=50):
        if not self._box:
            return []
        return self._load_history(peer_id)[-limit:]

    def _history_path(self, peer_id):
        return self.history_dir / f"{peer_id[:32]}.enc"

    def _load_history(self, peer_id):
        if peer_id in self._cache:
            return list(self._cache[peer_id])
        path = self._history_path(peer_id)
        if not path.exists():
            return []
        try:
            encrypted = path.read_bytes()
            plaintext = self.crypto.decrypt_from_storage(self._box, encrypted)
            data = json.loads(plaintext.decode('utf-8'))
            history = [ChatHistory.from_dict(d) for d in data]
            self._cache[peer_id] = history
            return list(history)
        except Exception as e:
            logger.error("Ошибка загрузки истории: %s", e)
            return []

    def _save_history(self, peer_id, history):
        try:
            plaintext = json.dumps([e.to_dict() for e in history], ensure_ascii=False).encode('utf-8')
            encrypted = self.crypto.encrypt_for_storage(self._box, plaintext)
            path = self._history_path(peer_id)
            path.write_bytes(encrypted)
            try:
                path.chmod(0o600)
            except Exception:
                pass
            self._cache[peer_id] = history
        except Exception as e:
            logger.error("Ошибка сохранения истории: %s", e)

    def list_chats(self):
        return [f.stem for f in self.history_dir.glob("*.enc")]

    def delete_history(self, peer_id):
        path = self._history_path(peer_id)
        if path.exists():
            size = path.stat().st_size
            path.write_bytes(b'\x00' * size)
            path.unlink()
        self._cache.pop(peer_id, None)
