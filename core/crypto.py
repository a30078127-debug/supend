"""
Крипто-ядро P2P мессенджера.

Используем libsodium через PyNaCl:
  - X25519 (Curve25519 DH) для обмена ключами
  - XSalsa20-Poly1305 для аутентифицированного шифрования
  - Ed25519 для подписи (верификация подлинности пира)

Принцип работы:
1. Каждый узел имеет постоянную пару Ed25519 (identity) — публичный ключ = адрес в сети
2. При каждом СЕАНСЕ генерируется эфемерная пара X25519 (ephemeral)
3. Обе стороны обмениваются эфемерными публичными ключами
4. Вычисляется общий секрет X25519 DH — это и есть сеансовый ключ
5. Все сообщения шифруются Box (XSalsa20-Poly1305) с уникальным nonce
6. Для защиты от replay-атак — nonce инкрементируется строго монотонно
"""

import os
import json
import time
import struct
import base64
import ctypes
import logging
from pathlib import Path
from dataclasses import dataclass, field

import nacl.utils
import nacl.secret
import nacl.public
import nacl.signing
import nacl.encoding
import nacl.hash
from nacl.bindings import crypto_kx_client_session_keys, crypto_kx_server_session_keys

logger = logging.getLogger(__name__)


def _secure_zero(data: bytearray) -> None:
    """Безопасно затираем чувствительные данные в памяти."""
    if isinstance(data, (bytearray, memoryview)):
        length = len(data)
        if length > 0:
            ctypes.memset((ctypes.c_char * length).from_buffer(data), 0, length)


@dataclass
class SessionKeys:
    """Сеансовые ключи, вычисленные через X25519 DH."""
    tx_key: bytearray
    rx_key: bytearray
    send_nonce: int = 0
    recv_nonce: int = 0

    def destroy(self) -> None:
        """Безопасно уничтожаем ключи после завершения сеанса."""
        _secure_zero(self.tx_key)
        _secure_zero(self.rx_key)
        self.send_nonce = 0
        self.recv_nonce = 0


class CryptoCore:
    """Главный криптографический класс."""

    NONCE_SIZE = nacl.secret.SecretBox.NONCE_SIZE

    def __init__(self, keys_path=None):
        self.keys_path = keys_path or Path("identity.key")
        self._identity_signing_key = None
        self._identity_verify_key = None
        self._load_or_generate_identity()

    def _load_or_generate_identity(self):
        if self.keys_path.exists():
            try:
                raw = self.keys_path.read_bytes()
                self._identity_signing_key = nacl.signing.SigningKey(raw)
                self._identity_verify_key = self._identity_signing_key.verify_key
                logger.info("Identity ключи загружены из %s", self.keys_path)
                return
            except Exception as e:
                logger.warning("Не удалось загрузить ключи: %s. Генерируем новые.", e)

        self._identity_signing_key = nacl.signing.SigningKey.generate()
        self._identity_verify_key = self._identity_signing_key.verify_key
        seed = bytes(self._identity_signing_key)
        self.keys_path.write_bytes(seed)
        try:
            self.keys_path.chmod(0o600)
        except Exception:
            pass
        logger.info("Новый identity создан: %s", self.get_peer_id())

    @property
    def peer_id(self):
        return self.get_peer_id()

    def get_peer_id(self):
        return bytes(self._identity_verify_key).hex()

    def get_public_key_bytes(self):
        return bytes(self._identity_verify_key)

    def generate_ephemeral_keypair(self):
        """Генерирует эфемерную пару X25519 для одного сеанса (PFS)."""
        private_key = nacl.public.PrivateKey.generate()
        return private_key, private_key.public_key

    def compute_session_keys(self, our_private, their_public, we_are_initiator):
        """Вычисляет сеансовые ключи через X25519 DH."""
        our_pk_bytes = bytes(our_private.public_key)
        our_sk_bytes = bytes(our_private)
        their_pk_bytes = bytes(their_public)

        if we_are_initiator:
            rx, tx = crypto_kx_client_session_keys(our_pk_bytes, our_sk_bytes, their_pk_bytes)
        else:
            rx, tx = crypto_kx_server_session_keys(our_pk_bytes, our_sk_bytes, their_pk_bytes)

        return SessionKeys(tx_key=bytearray(tx), rx_key=bytearray(rx))

    def _make_nonce(self, counter):
        """Формирует 24-байтный nonce из монотонного счётчика."""
        return b'\x00' * 16 + struct.pack('>Q', counter)

    def encrypt(self, session, plaintext):
        """Шифрует plaintext с аутентификацией (AEAD XSalsa20-Poly1305)."""
        session.send_nonce += 1
        nonce = self._make_nonce(session.send_nonce)
        box = nacl.secret.SecretBox(bytes(session.tx_key))
        ciphertext = box.encrypt(plaintext, nonce)
        return struct.pack('>Q', session.send_nonce) + ciphertext.ciphertext

    def decrypt(self, session, data):
        """Расшифровывает и верифицирует аутентичность. Защита от replay."""
        if len(data) < 8 + 16:
            raise ValueError("Сообщение слишком короткое")
        counter = struct.unpack('>Q', data[:8])[0]
        encrypted_payload = data[8:]
        if counter <= session.recv_nonce:
            raise ValueError(f"Replay-атака! counter={counter}, ожидалось > {session.recv_nonce}")
        nonce = self._make_nonce(counter)
        box = nacl.secret.SecretBox(bytes(session.rx_key))
        plaintext = box.decrypt(encrypted_payload, nonce)
        session.recv_nonce = counter
        return plaintext

    def sign(self, data):
        """Подписываем данные Ed25519 приватным ключом."""
        signed = self._identity_signing_key.sign(data)
        return signed.signature

    def verify(self, peer_public_key_bytes, data, signature):
        """Верифицируем подпись пира его публичным ключом."""
        try:
            verify_key = nacl.signing.VerifyKey(peer_public_key_bytes)
            verify_key.verify(data, signature)
            return True
        except nacl.exceptions.BadSignatureError:
            return False

    def derive_storage_key(self, password):
        """Выводит ключ шифрования хранилища из пароля."""
        person = self.get_public_key_bytes()[:16]
        key = nacl.hash.blake2b(
            password.encode('utf-8'),
            digest_size=32,
            person=person,
            encoder=nacl.encoding.RawEncoder,
        )
        return nacl.secret.SecretBox(key)

    def encrypt_for_storage(self, box, data):
        return box.encrypt(data)

    def decrypt_from_storage(self, box, data):
        return box.decrypt(data)

    def create_handshake_payload(self, ephemeral_public):
        """Формирует данные для handshake с подписью."""
        ephemeral_bytes = bytes(ephemeral_public)
        timestamp = int(time.time())
        sign_data = ephemeral_bytes + struct.pack('>Q', timestamp)
        signature = self.sign(sign_data)
        return {
            "identity_key": self.get_public_key_bytes().hex(),
            "ephemeral_key": ephemeral_bytes.hex(),
            "timestamp": timestamp,
            "signature": signature.hex(),
        }

    def verify_handshake_payload(self, payload):
        """Верифицирует handshake от пира."""
        try:
            identity_bytes = bytes.fromhex(payload["identity_key"])
            ephemeral_bytes = bytes.fromhex(payload["ephemeral_key"])
            timestamp = payload["timestamp"]
            signature = bytes.fromhex(payload["signature"])
            now = int(time.time())
            if abs(now - timestamp) > 30:
                return False, b'', b''
            sign_data = ephemeral_bytes + struct.pack('>Q', timestamp)
            if not self.verify(identity_bytes, sign_data, signature):
                return False, b'', b''
            return True, identity_bytes, ephemeral_bytes
        except (KeyError, ValueError):
            return False, b'', b''
