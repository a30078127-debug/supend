"""Консольный интерфейс P2P мессенджера."""

import asyncio
import logging
import os
import time
from datetime import datetime

logger = logging.getLogger(__name__)


def _ts_str(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


class ConsoleUI:
    PROMPT = ">>> "
    DIVIDER = "─" * 60

    def __init__(self, node, storage, tracker=None):
        self.node = node
        self.storage = storage
        self.tracker = tracker
        self._current_peer = None
        self._running = False

    async def run(self):
        self.node.on_message(self._on_message)
        self.node.on_connect(self._on_peer_connect)
        self.node.on_disconnect(self._on_peer_disconnect)
        self._running = True
        self._print_banner()

        while self._running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, self._read_line)
                if line is None:
                    break
                line = line.strip()
                if not line:
                    continue
                await self._handle_input(line)
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                self._print(f"[!] Ошибка: {e}")
        self._running = False

    def _read_line(self):
        try:
            return input(self.PROMPT)
        except (EOFError, KeyboardInterrupt):
            return None

    async def _handle_input(self, line):
        if line.startswith("/"):
            parts = line.split(maxsplit=2)
            await self._handle_command(parts[0].lower(), parts[1:])
        else:
            await self._send_message(line)

    async def _handle_command(self, cmd, args):
        if cmd == "/help":
            self._print_help()
        elif cmd == "/myid":
            self._print(f"Ваш ID: {self.node.peer_id}")
            self._print(f"Порт:   {self.node.port}")
        elif cmd == "/peers":
            await self._cmd_peers()
        elif cmd == "/connect":
            await self._cmd_connect(args)
        elif cmd == "/chat":
            await self._cmd_chat(args)
        elif cmd == "/history":
            await self._cmd_history()
        elif cmd == "/chats":
            chats = self.storage.list_chats()
            self._print(f"Чаты: {chats if chats else 'пусто'}")
        elif cmd == "/disconnect":
            await self._cmd_disconnect()
        elif cmd == "/tracker":
            await self._cmd_tracker(args)
        elif cmd == "/register":
            await self._cmd_register()
        elif cmd == "/discover":
            await self._cmd_discover()
        elif cmd == "/clear":
            os.system('cls' if os.name == 'nt' else 'clear')
        elif cmd in ("/quit", "/exit"):
            self._print("До свидания!")
            self._running = False
        else:
            self._print(f"Неизвестная команда: {cmd}. Введите /help")

    async def _cmd_peers(self):
        peers = self.node.peers
        if not peers:
            self._print("Нет подключённых пиров")
            return
        self._print(f"Подключено: {len(peers)}")
        for pid, conn in peers.items():
            info = conn.peer_info
            mark = "●" if pid == self._current_peer else " "
            self._print(f"  {mark} {pid[:16]}... @ {info.host}:{info.port}")

    async def _cmd_connect(self, args):
        if len(args) == 2:
            host, port = args[0], int(args[1])
            self._print(f"Подключаемся к {host}:{port}...")
            ok = await self.node.connect_to(host, port)
            if not ok:
                self._print("Не удалось подключиться")
        elif len(args) == 1 and self.tracker:
            found = await self.tracker.lookup(args[0])
            if found:
                info = found[0]
                ok = await self.node.connect_to(info['ip'], info['port'])
                if not ok:
                    self._print("Не удалось подключиться")
            else:
                self._print("Пир не найден")
        else:
            self._print("Использование: /connect <host> <port>")

    async def _cmd_chat(self, args):
        if not args:
            self._print(f"Текущий чат: {self._current_peer[:32] if self._current_peer else 'нет'}")
            return
        prefix = args[0].lower()
        matches = [pid for pid in self.node.peers if pid.startswith(prefix)]
        if not matches:
            self._print("Пир не найден")
        elif len(matches) > 1:
            self._print("Неоднозначный ID")
        else:
            self._current_peer = matches[0]
            self._print(f"Активный чат: {self._current_peer[:32]}...")
            await self._cmd_history(limit=10)

    async def _cmd_history(self, limit=20):
        if not self._current_peer:
            self._print("Нет активного чата")
            return
        history = self.storage.load_history(self._current_peer, limit=limit)
        if not history:
            self._print("История пуста")
            return
        self._print(self.DIVIDER)
        for entry in history:
            who = "Я" if entry.is_outgoing else entry.peer_id[:8] + "..."
            self._print(f"[{_ts_str(entry.timestamp)}] {who}: {entry.text}")
        self._print(self.DIVIDER)

    async def _cmd_disconnect(self):
        if not self._current_peer:
            self._print("Нет активного чата")
            return
        await self.node.disconnect_peer(self._current_peer)
        self._print(f"Отключились от {self._current_peer[:16]}...")
        self._current_peer = None

    async def _cmd_tracker(self, args):
        if len(args) < 2:
            self._print("Использование: /tracker <host> <port>")
            return
        from network.tracker import TrackerClient
        self.tracker = TrackerClient(args[0], int(args[1]))
        self._print(f"Трекер: {args[0]}:{args[1]}")

    async def _cmd_register(self):
        if not self.tracker:
            self._print("Сначала: /tracker <host> <port>")
            return
        ok = await self.tracker.register(self.node.peer_id, self.node.port)
        self._print("Зарегистрированы!" if ok else "Ошибка регистрации")

    async def _cmd_discover(self):
        if not self.tracker:
            self._print("Сначала: /tracker <host> <port>")
            return
        peers = await self.tracker.lookup("*")
        if not peers:
            self._print("Пиры не найдены")
        else:
            for p in peers:
                self._print(f"  {p['id'][:16]}... @ {p['ip']}:{p['port']}")

    async def _send_message(self, text):
        if not self._current_peer:
            self._print("Нет активного чата. /connect <host> <port>")
            return
        ok = await self.node.send_to(self._current_peer, text)
        if ok:
            self.storage.save_message(self._current_peer, text, is_outgoing=True)
            print(f"\r[{_ts_str(int(time.time()))}] Я: {text}")
        else:
            self._print("Ошибка отправки")

    async def _on_message(self, peer_id, msg):
        self.storage.save_message(peer_id, msg.text, is_outgoing=False)
        short = peer_id[:8] + "..."
        if peer_id == self._current_peer:
            print(f"\r[{_ts_str(msg.timestamp)}] {short}: {msg.text}")
        else:
            print(f"\r[!] Новое сообщение от {short}")
        print(self.PROMPT, end='', flush=True)

    async def _on_peer_connect(self, info):
        short = info.peer_id[:16] + "..."
        self._print(f"\n[+] Подключился: {short} @ {info.host}:{info.port}")
        if not self._current_peer:
            self._current_peer = info.peer_id
            self._print(f"[*] Активный чат: {short}")

    async def _on_peer_disconnect(self, peer_id):
        self._print(f"\n[-] Отключился: {peer_id[:16]}...")
        if self._current_peer == peer_id:
            self._current_peer = None
            self._print("[*] Нет активного чата")

    def _print(self, text):
        print(f"\r{text}")
        if self._running:
            print(self.PROMPT, end='', flush=True)

    def _print_banner(self):
        print(self.DIVIDER)
        print("  P2P Анонимный Мессенджер")
        print(f"  Ваш ID: {self.node.peer_id[:32]}...")
        print(f"  Порт:   {self.node.port}")
        print(self.DIVIDER)
        print("  /help — список команд")
        print(self.DIVIDER)

    def _print_help(self):
        print("""
  /connect <host> <port>  — подключиться к другу
  /peers                  — кто подключён
  /chat <первые буквы ID> — переключить чат
  /history                — история сообщений
  /disconnect             — отключиться
  /myid                   — твой ID и порт
  /discover               — найти через трекер
  /clear                  — очистить экран
  /quit                   — выйти
  
  Просто пиши текст — это отправка сообщения!
""")
