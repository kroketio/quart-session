# -*- coding: utf-8 -*-
"""
    quart_session.redis_trio.errors
    ~~~~~~~~~~~~~~~~~~~~~~

    A simple Redis Trio client.

    :copyright: (c) 2017 by Bogdan Paul Popa.
    :copyright: (c) 2019 by Oleksii Aleksieiev.
    :copyright: (c) 2020 by dsc.
    :license: BSD, see LICENSE for more details.
"""


class RedisError(Exception):
    """Base class for all Redis-related errors.
    """


class ProtocolError(RedisError):
    """Raised when Redis responds with something that doesn't conform
    to the protocol.
    """


class ResponseError(RedisError):
    """Raised when Redis returns an error response.
    """


class ResponseTypeError(ResponseError):
    """Raised when Redis returns an error response with a `WRONGTYPE` prefix.
    """
