import asyncio
import sys


def run(coroutine):
    # Psycopg's async sockets need SelectorEventLoop on Windows.
    if sys.platform == "win32":
        return asyncio.run(coroutine, loop_factory=asyncio.SelectorEventLoop)
    return asyncio.run(coroutine)
