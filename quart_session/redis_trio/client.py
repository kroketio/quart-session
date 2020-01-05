# -*- coding: utf-8 -*-
"""
    quart_session.redis_trio
    ~~~~~~~~~~~~~~~~~~~~~~

    A simple Redis Trio client.

    :copyright: (c) 2017 by Bogdan Paul Popa.
    :copyright: (c) 2019 by Oleksii Aleksieiev.
    :copyright: (c) 2020 by dsc.
    :license: BSD, see LICENSE for more details.
"""
from typing import Union

from .connection import RedisConnection


class RedisTrio:
    """A simple Redis+Trio client.

    Parameters:
      addr(str): The IP address the Redis server is listening on.
      port(int): The port the Redis server is listening on.

    Examples:

      >>> async with RedisTrio() as redis:
      ...   await redis.set("foo", 42)
      ...   await redis.get("foo")
      b'42'
    """

    def __init__(self, addr: Union[bytes, str] = b"127.0.0.1", port: int = 6379, password: bytes = b""):
        self.conn = RedisConnection(addr, port)
        self.password = password

    async def connect(self):
        """Open a connection to the Redis server.

        Returns:
          RedisTrio: This instance.
        """
        await self.conn.connect()
        if self.password:
            await self.auth(self.password)
        return self

    async def close(self):
        """Close the connection to the Redis server.
        """
        await self.quit()
        self.conn.close()

    async def auth(self, password):
        return await self.conn.process_command_ok(b"AUTH", password)

    async def delete(self, *keys):
        return await self.conn.process_command(b"DEL", *keys)

    async def echo(self, message):
        return await self.conn.process_command(b"ECHO", message)

    async def flushall(self):
        return await self.conn.process_command_ok(b"FLUSHALL")

    async def get(self, key) -> bytes:
        return await self.conn.process_command(b"GET", key)

    async def quit(self):
        return await self.conn.process_command(b"QUIT")

    async def set(self, key, value):
        return await self.conn.process_command_ok(b"SET", key, value)

    async def setex(self, key: str, value: str, seconds: int):
        """Set the value and expiration of a key.
        :raises TypeError: if seconds is not int
        """
        if not isinstance(seconds, int):
            raise TypeError("milliseconds argument must be int")

        return await self.conn.process_command_ok(b"SETEX", key, seconds, value)

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()
