# -*- coding: utf-8 -*-
"""
    quart_session
    ~~~~~~~~~~~~~

    Adds server session support to your application.

    :copyright: (c) 2014 by Shipeng Feng.
    :copyright: (c) 2020 by dsc.
    :license: BSD, see LICENSE for more details.
"""

__version__ = '1.0.0'

import os

from quart import Quart

from .sessions import RedisSessionInterface, RedisTrioSessionInterface, MemcachedSessionInterface, NullSessionInterface


class Session(object):
    """This class is used to add Server-side Session to one or more Quart
    applications.

    There are two usage modes.  One is initialize the instance with a very
    specific Quart application::

        app = Quart(__name__)
        Session(app)

    The second possibility is to create the object once and configure the
    application later::

        sess = Session()

        def create_app():
            app = Quart(__name__)
            sess.init_app(app)
            return app

    By default Quart-Session will use :class:`NullSessionInterface`, you
    really should configure your app to use a different SessionInterface.

    .. note::

        You can not use ``Session`` instance directly, what ``Session`` does
        is just change the :attr:`~quart.Quart.session_interface` attribute on
        your Quart applications.
    """

    def __init__(self, app: Quart = None) -> None:
        self._current_async_library = "asyncio"
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:
        """This is used to set up session for your app object.

        :param app: the Quart app object with proper configuration.
        """
        try:
            import quart_trio
            if isinstance(app, quart_trio.QuartTrio):
                self._current_async_library = "trio"
        except ImportError:
            pass
        app.session_interface = self._get_interface(app)

        @app.before_serving
        async def setup():
            await app.session_interface.create(app)

    def _get_interface(self, app: Quart):
        config = app.config.copy()
        config.setdefault('SESSION_TYPE', 'null')
        config.setdefault('SESSION_PERMANENT', True)
        config.setdefault('SESSION_USE_SIGNER', False)
        config.setdefault('SESSION_KEY_PREFIX', 'session:')
        config.setdefault('SESSION_PROTECTION', False)
        config.setdefault('SESSION_REVERSE_PROXY', False)
        config.setdefault('SESSION_STATIC_FILE', False)
        config.setdefault('SESSION_EXPLICIT', False)
        config.setdefault('SESSION_REDIS', None)
        config.setdefault('SESSION_MEMCACHED', None)
        config.setdefault('SESSION_FILE_DIR',
                          os.path.join(os.getcwd(), 'quart_session'))
        config.setdefault('SESSION_FILE_THRESHOLD', 500)
        config.setdefault('SESSION_FILE_MODE', 384)
        config = {k: v for k, v in config.items() if k.startswith('SESSION_')}

        if isinstance(config.get("SESSION_HIJACK_PROTECTION"), bool):
            app.logger.warning("Deprecation: `SESSION_HIJACK_PROTECTION` "
                               "has been renamed to `SESSION_PROTECTION`")

        if isinstance(config.get("SESSION_HIJACK_REVERSE_PROXY"), str):
            app.logger.warning("Deprecation: `SESSION_HIJACK_REVERSE_PROXY` "
                               "has been renamed to `SESSION_REVERSE_PROXY`")

        if config['SESSION_TYPE'] == 'redis':
            options = {
                "redis": config['SESSION_REDIS'],
                "key_prefix": config['SESSION_KEY_PREFIX'],
                "use_signer": config['SESSION_USE_SIGNER'],
                "permanent": config['SESSION_PERMANENT'],
                **config
            }

            if self._current_async_library == "asyncio":
                session_interface = RedisSessionInterface(**options)
            elif self._current_async_library == "trio":
                session_interface = RedisTrioSessionInterface(**options)
            else:
                raise NotImplementedError("Unknown eventloop")

        elif config['SESSION_TYPE'] == 'redis+trio':
            session_interface = RedisTrioSessionInterface(
                redis=config['SESSION_REDIS'],
                key_prefix=config['SESSION_KEY_PREFIX'],
                use_signer=config['SESSION_USE_SIGNER'],
                premanent=config['SESSION_PERMANENT'],
                **config
            )
        elif config['SESSION_TYPE'] == 'memcached':
            session_interface = MemcachedSessionInterface(
                memcached=config['SESSION_MEMCACHED'],
                key_prefix=config['SESSION_KEY_PREFIX'],
                use_signer=config['SESSION_USE_SIGNER'],
                permanent=config['SESSION_PERMANENT'],
                **config)
        else:
            session_interface = NullSessionInterface()

        return session_interface
