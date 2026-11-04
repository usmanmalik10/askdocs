import asyncio
import sys

from runtime import run


def test_runtime_uses_a_database_compatible_event_loop():
    async def inspect():
        loop = asyncio.get_running_loop()
        return isinstance(loop, asyncio.SelectorEventLoop) if sys.platform == "win32" else loop.is_running()
    assert run(inspect()) is True
