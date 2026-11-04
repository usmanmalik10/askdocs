import asyncio
import sys


def pytest_asyncio_loop_factories(config, item):
    return {"database-compatible": asyncio.SelectorEventLoop if sys.platform == "win32" else asyncio.new_event_loop}
