"""Точка входа трекера для Railway."""
import asyncio
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from tracker import TrackerServer

async def main():
    port = int(os.environ.get("PORT", 9000))
    server = TrackerServer(host="0.0.0.0", port=port)
    print(f"[*] Трекер запускается на порту {port}")
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
