"""P2P Анонимный Мессенджер."""

import argparse
import asyncio
import logging
from pathlib import Path

from core.crypto import CryptoCore
from network.node import P2PNode
from network.tracker import TrackerClient, TrackerServer
from storage.history import EncryptedStorage
from ui.console import ConsoleUI


def setup_logging(debug=False):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.WARNING,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )


async def run_messenger(args):
    data_dir = Path.home() / ".p2p_messenger"
    data_dir.mkdir(mode=0o700, exist_ok=True)

    crypto = CryptoCore(keys_path=data_dir / "identity.key")
    print(f"[*] Ваш ID: {crypto.peer_id}")

    storage = EncryptedStorage(crypto, base_dir=data_dir)
    if not args.no_history:
        try:
            password = input("Пароль для истории (Enter = не сохранять): ").strip()
            if password:
                storage.unlock(password)
                print("[*] История включена")
            else:
                print("[!] История не будет сохраняться")
        except (EOFError, KeyboardInterrupt):
            print()

    tracker = None
    if args.tracker:
        parts = args.tracker.split(":")
        tracker = TrackerClient(parts[0], int(parts[1]) if len(parts) > 1 else 9000)
        print(f"[*] Трекер: {args.tracker}")

    node = P2PNode(crypto=crypto, host="0.0.0.0", port=args.port)
    actual_port = await node.start()
    print(f"[*] Слушаем на порту {actual_port}")

    if tracker:
        ok = await tracker.register(crypto.peer_id, actual_port)
        print("[*] Зарегистрированы на трекере" if ok else "[!] Трекер недоступен")

    # ── Выбор интерфейса ──────────────────────────────────
    if args.gui:
        from ui.gui import GUIServer
        ui = GUIServer(node=node, storage=storage, tracker=tracker,
                       host='0.0.0.0', port=args.gui_port)
        print(f"[*] Запускаем GUI на http://127.0.0.1:{args.gui_port}")
        try:
            await ui.run()
        finally:
            print("\n[*] Завершаем...")
            await node.stop()
            storage.lock()
    else:
        ui = ConsoleUI(node=node, storage=storage, tracker=tracker)
        try:
            await ui.run()
        finally:
            print("\n[*] Завершаем...")
            await node.stop()
            storage.lock()


async def run_tracker(args):
    t = TrackerServer(host="0.0.0.0", port=args.port)
    print(f"[*] Трекер на порту {args.port} (Ctrl+C для остановки)")
    try:
        await t.start()
    except KeyboardInterrupt:
        print("\n[*] Трекер остановлен")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port",       type=int,  default=0,
                   help="Порт P2P ноды (0 = авто)")
    p.add_argument("--tracker",    type=str,  default=None,
                   help="Адрес трекера host:port")
    p.add_argument("--run-tracker",action="store_true",
                   help="Запустить в режиме трекера")
    p.add_argument("--no-history", action="store_true",
                   help="Не сохранять историю")
    p.add_argument("--debug",      action="store_true",
                   help="Подробные логи")
    # ── Новые флаги ──────────────────────────────────────
    p.add_argument("--gui",        action="store_true",
                   help="Запустить GUI в браузере вместо консоли")
    p.add_argument("--gui-port",   type=int,  default=8765,
                   help="Порт GUI-сервера (по умолчанию 8765)")

    args = p.parse_args()
    setup_logging(args.debug)

    if args.run_tracker:
        if args.port == 0:
            args.port = 9000
        asyncio.run(run_tracker(args))
    else:
        asyncio.run(run_messenger(args))


if __name__ == "__main__":
    main()
