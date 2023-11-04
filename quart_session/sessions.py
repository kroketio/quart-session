# -*- coding: utf-8 -*-
"""
    quart_session.sessions
    ~~~~~~~~~~~~~~~~~~~~~~

    Server-side Sessions and SessionInterfaces.

    :copyright: (c) 2014 by Shipeng Feng.
    :copyright: (c) 2020 by Kroket Ltd.
    :license: BSD, see LICENSE for more details.
"""
import time
from typing import Optional
from uuid import uuid4, UUID
import asyncio
import functools

from quart import Quart, current_app
from quart.wrappers import BaseRequestWebsocket, Response
from quart.wrappers.response import FileBody
from quart.sessions import SessionInterface as QuartSessionInterface, SecureCookieSession
from quart.json.tag import TaggedJSONSerializer
from itsdangerous import Signer, BadSignature, want_bytes


def total_seconds(td):
    return td.days * 60 * 60 * 24 + td.seconds


class ServerSideSession(SecureCookieSession):
    """Baseclass for server-side based sessions."""

    def __init__(self, initial=None, sid=None, permanent=None, addr=None):
        super(ServerSideSession, self).__init__(initial or {})
        self.sid = sid
        if permanent:
            self.permanent = permanent
        if addr:
            self.addr = addr
        self.modified = False

    def dirty(self):
        current_app.logger.warning("Deprecation: `dirty()` has "
                                   "been made obsolete. Will be "
                                   "removed soon^tm.")

    @property
    def addr(self) -> str:
        return self.get('_addr', False)  # type: ignore

    @addr.setter
    def addr(self, value: str) -> None:
        self['_addr'] = value  # type: ignore


class RedisSession(ServerSideSession):
    pass


class MemcachedSession(ServerSideSession):
    pass


class MongoDBSession(ServerSideSession):
    pass


class NullSession(ServerSideSession):
    pass


class SessionInterface(QuartSessionInterface):
    """Baseclass for session interfaces"""

    serializer = TaggedJSONSerializer()
    session_class = None

    def __init__(
            self,
            key_prefix: str,
            use_signer: bool = False,
            permanent: bool = True,
            **kwargs
    ) -> None:
        self.key_prefix = key_prefix
        self.use_signer = use_signer
        self.permanent = permanent
        self._config = kwargs

    async def open_session(
            self,
            app: Quart,
            request: BaseRequestWebsocket
    ) -> Optional[SecureCookieSession]:
        cname = app.config.get('SESSION_COOKIE_NAME', 'session')
        sid = request.cookies.get(cname)
        if self._config['SESSION_REVERSE_PROXY'] is True:
            # and no, you cannot define your own incoming
            # header, stick to standards :-)
            addr = request.headers.get('X-Forwarded-For')
            if not addr:
                app.logger.error("Could not grab IP from reverse proxy, "
                                 "session protection is DISABLED!")
        else:
            addr = request.remote_addr
        options = {"sid": sid, "permanent": self.permanent, "addr": addr}

        if not sid:
            options['sid'] = self._generate_sid()
            return self.session_class(**options)
        if self.use_signer:
            signer = self._get_signer(app)
            if signer is None:
                app.logger.warning("Failed to obtain a valid signer.")
                return None
            try:
                sid_as_bytes = signer.unsign(sid)
                sid = sid_as_bytes.decode()
            except BadSignature:
                app.logger.warning(f"Bad signature for sid: {sid}.")
                options['sid'] = self._generate_sid()
                return self.session_class(**options)

        val = await self.get(key=self.key_prefix + sid, app=app)
        if val is None:
            options['sid'] = self._generate_sid()
            return self.session_class(**options)

        if self.serializer is None:
            data = val
        else:
            try:
                data = self.serializer.loads(val)
            except:
                app.logger.warning(f"Failed to deserialize session "
                                   f"data for sid: {sid}. Generating new sid.")
                app.logger.debug(f"data: {val}")
                options['sid'] = self._generate_sid()
                return self.session_class(**options)

        protection = self._config['SESSION_PROTECTION']
        if protection is True and addr is not None and \
                data.get('_addr', addr) != addr:
            await self.delete(key=self.key_prefix + sid, app=app)
            options['sid'] = self._generate_sid()
            return self.session_class(**options)

        res = self.session_class(data, sid)
        return res

    async def save_session(  # type: ignore
        self,
        app: "Quart",
        session: SecureCookieSession,
        response: Response
    ) -> None:
        # prevent set-cookie on unmodified session objects
        if not session.modified:
            return

        # prevent set-cookie on (static) file responses
        # https://github.com/fengsp/flask-session/pull/70
        if self._config['SESSION_STATIC_FILE'] is False and \
                isinstance(response.response, FileBody):
            return

        cname = app.config.get('SESSION_COOKIE_NAME', 'session')
        session_key = self.key_prefix + session.sid
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        if not session:
            if session.modified:
                await self.delete(key=session_key, app=app)
                response.delete_cookie(cname,
                                       domain=domain, path=path)
            return
        httponly = self.get_cookie_httponly(app)
        samesite = self.get_cookie_samesite(app)
        secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session)

        if self.serializer is None:
            val = dict(session)
        else:
            val = self.serializer.dumps(dict(session))

        await self.set(key=session_key, value=val, app=app)
        if self.use_signer:
            session_id = self._get_signer(app).sign(want_bytes(session.sid))
        else:
            session_id = session.sid
        response.set_cookie(cname, session_id,
                            expires=expires, httponly=httponly,
                            domain=domain, path=path, secure=secure, samesite=samesite)

    async def create(self, app: Quart):
        raise NotImplementedError()

    async def get(self, key: str, app: Quart = None):
        raise NotImplementedError()

    async def set(self, key: str, value, expiry: int = None,
                  app: Quart = None):
        raise NotImplementedError()

    async def delete(self, key: str, app: Quart = None):
        raise NotImplementedError()

    def _generate_sid(self) -> str:
        return str(uuid4())

    def _get_signer(self, app) -> Optional[Signer]:
        if not app.secret_key:
            return None
        return Signer(app.secret_key, salt='quart-session',
                      key_derivation='hmac')


class RedisSessionInterface(SessionInterface):
    """Uses the Redis key-value store as a session backend.

    :param redis: ``aioredis.Redis`` instance.
    :param key_prefix: A prefix that is added to all Redis store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    :param kwargs: Quart-session config, used internally.
    """

    session_class = RedisSession

    def __init__(self, redis, **kwargs):
        super(RedisSessionInterface, self).__init__(**kwargs)
        self.backend = redis

    async def create(self, app: Quart) -> None:
        """Creates ``aioredis.Redis`` instance.

        .. note::

            Creates a single Redis connection, you might prefer
            pooling instead (see the `aioredis` documentation
            for connection pool examples).
        """
        if self.backend is None:
            from redis import asyncio as aioredis
            uri = self._config.get('SESSION_URI', 'redis://localhost')
            self.backend = await aioredis.from_url(
                uri, encoding="utf-8", decode_responses=True
            )

    async def get(self, key: str, app: Quart = None):
        return await self.backend.get(key)

    async def set(self, key: str, value, expiry: int = None,
                  app: Quart = None):
        if app and not expiry:
            expiry = total_seconds(app.permanent_session_lifetime)
        return await self.backend.setex(
            name=key, value=value,
            time=expiry)

    async def delete(self, key: str, app: Quart = None):
        return await self.backend.delete(key)


class RedisTrioSessionInterface(SessionInterface):
    """Uses the Redis+Trio key-value store as a session backend.

    :param redis: ``quart_session.redis_trio.RedisTrio`` instance.
    :param key_prefix: A prefix that is added to all Redis store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    :param kwargs: Quart-session config, used internally.
    """

    session_class = RedisSession

    def __init__(self, redis, **kwargs):
        super(RedisTrioSessionInterface, self).__init__(**kwargs)
        self.backend = redis

    async def create(self, app: Quart) -> None:
        """Creates ``aioredis.Redis`` instance.

        .. note::

            Creates a single Redis connection. Pooling not
            supported yet for ``RedisTrio``.
        """
        if self.backend is None:
            from quart_session.redis_trio import RedisTrio
            self.backend = RedisTrio()
            await self.backend.connect()

    async def get(self, key: str, app: Quart = None):
        data = await self.backend.get(key)
        if data:
            return data.decode()

    async def set(self, key: str, value, expiry: int = None,
                  app: Quart = None):
        if app and not expiry:
            expiry = total_seconds(app.permanent_session_lifetime)
        return await self.backend.setex(
            key=key, value=value,
            seconds=expiry)

    async def delete(self, key: str, app: Quart = None):
        return await self.backend.delete(key)


class MemcachedSessionInterface(SessionInterface):
    """Uses the Memcached key-value store as a session backend.

    :param client: ``aiomcache.Client`` instance.
    :param key_prefix: A prefix that is added to all Redis store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    :param kwargs: Quart-session config, used internally.
    """

    session_class = MemcachedSession

    def __init__(
            self, memcached, key_prefix: str, use_signer: bool = False,
            permanent: bool = True, **kwargs):
        super(MemcachedSessionInterface, self).__init__(
            key_prefix=key_prefix, use_signer=use_signer,
            permanent=permanent, **kwargs)
        self.backend = memcached

    async def create(self, app: Quart) -> None:
        if self.backend is None:
            import aiomcache
            # self.backend = aiomcache.Client("127.0.0.1", 11211)
            self.backend = aiomcache.Client(self._config.get('SESSION_MEMCACHED_HOST', '127.0.0.1'),
                                            self._config.get('SESSION_MEMCACHED_PORT', 11211))

    def _get_memcache_timeout(self, timeout):
        """
        Memcached deals with long (> 30 days) timeouts in a special
        way. Call this function to obtain a safe value for your timeout.
        """
        if timeout > 2592000:  # 60*60*24*30, 30 days
            # See http://code.google.com/p/memcached/wiki/FAQ
            # "You can set expire times up to 30 days in the future. After that
            # memcached interprets it as a date, and will expire the item after
            # said date. This is a simple (but obscure) mechanic."
            #
            # This means that we have to switch to absolute timestamps.
            timeout += int(time.time())
        return timeout

    async def get(self, key: str, app: Quart = None):
        key = key.encode()
        return await self.backend.get(key)

    async def set(self, key: str, value, expiry: int = None,
                  app: Quart = None):
        if app and not expiry:
            expiry = self._get_memcache_timeout(
                total_seconds(app.permanent_session_lifetime))

        key = key.encode()
        value = value.encode()
        return await self.backend.set(key=key, value=value,
                                      exptime=expiry)

    async def delete(self, key: str, app: Quart = None):
        key = key.encode()
        return await self.backend.delete(key)


def _convert_key_to_uuid(func):
    """
        convert the session UUID to a UUID object for mongodb

        example:
            "session:b8ebbf02-cc7a-4b0b-824f-22a984c8c0b8" ->
            UUID("b8ebbf02-cc7a-4b0b-824f-22a984c8c0b8")

    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if 'key' in kwargs:
            key = kwargs['key']
            try:
                if key.startswith('session:'):
                    _, _uuid = tuple(key.split(':'))
                    kwargs['key'] = UUID(_uuid)
            except Exception as e:
                current_app.logger.warning(
                    f"session could not be converted to a uuid object: {key}"
                )
        return await func(*args, **kwargs)
    return wrapper


class MongoDBSessionInterface(SessionInterface):
    # mongodb does not a serializer as many object types are properly handled by the connector
    serializer = None
    session_class = MongoDBSession

    def __init__(self, mongodb_uri, collection, client_kwargs={}, set_callback=None, **kwargs):
        from motor.motor_asyncio import AsyncIOMotorClient

        super().__init__(**kwargs)
        self.mongodb_uri = mongodb_uri
        self.client_kwargs = client_kwargs
        self.set_callback = set_callback
        self._collection = collection
        self._client = AsyncIOMotorClient(self.mongodb_uri, uuidRepresentation='standard', **self.client_kwargs)
        self._database = self._client.get_database()

    async def create(self, app: Quart) -> None:
        pass

    @_convert_key_to_uuid
    async def get(self, key, app):
        value = await self.collection.find_one({'_id': key}, {'data': True})
        if value:
            return value.get('data', {})
        else:
            return None

    @_convert_key_to_uuid
    async def set(self, key, value, expiry=None, app=None):
        doc = {
            'data': value,
        }

        # allows the document to be modified prior upsert
        if callable(self.set_callback):
            self.set_callback(doc)

        await self.collection.update_one({
                '_id': key
            }, {
                '$set': doc
            },
            upsert=True
        )

    @property
    def collection(self):
        return self._database.get_collection(self._collection)


class NullSessionInterface(SessionInterface):
    """This class does absolutely nothing"""
    session_class = NullSession

    def __init__(
            self, key_prefix: str, use_signer: bool = False,
            permanent: bool = True, **kwargs):
        super(NullSessionInterface, self).__init__(
            key_prefix=key_prefix, use_signer=use_signer,
            permanent=permanent, **kwargs)
        self.backend = None

    async def create(self, app: Quart) -> None:
        pass

    async def get(self, key: str, app: Quart = None) -> None:
        pass

    async def set(self, key: str, value, expiry: int = None,
                  app: Quart = None) -> None:
        pass
