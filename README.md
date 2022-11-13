# Quart-Session

![pyversions](https://img.shields.io/pypi/pyversions/Quart-Session.svg) [![pypiversion](https://badge.fury.io/py/Quart-Session.svg)](https://pypi.org/project/Quart-Session/) ![PyPI license](https://img.shields.io/pypi/l/Quart-Session.svg)

Quart-Session is an extension for [Quart](https://gitlab.com/pgjones/quart/blob/master/README.rst) that adds support for
server-side sessions to your application.

Based on [flask-session](https://pypi.org/project/Flask-Session/).

## Quick start

Quart-Session can be installed via pipenv or pip,

```bash
$ pipenv install quart-session
$ pip install quart-session
```

and requires Python 3.7.0 or higher. A minimal Quart-Session example is:

```python3
from quart import Quart, session
from quart_session import Session

app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)

@app.route('/')
async def hello():
    session["foo"] = "bar"
    return "session key 'foo' set"

@app.route('/foo')
async def foo():
    return session.get("foo", "session key 'foo' not found")

app.run()
```

## Features


### Redis

via `aioredis>=2.0.0`.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)
```

By default, Quart-session connects to Redis at `127.0.0.1:6379`. If you 
have a different location, use `SESSION_URI`

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_URI'] = 'redis://:password@localhost:6379'
```

Alternatively, for extra control, you may provide your own `aioredis.Client` instance altogether.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'

@app.before_serving
async def setup():
    cache = await aioredis.Redis(
        host="foobar.com",
        port=6379,
        password="foobar"
    )
    
    app.config['SESSION_REDIS'] = cache
    Session(app)
```

#### Trio

Quart-Session comes with [an (experimental) Redis client](quart_session/redis_trio) for use with the [Trio](https://trio.readthedocs.io/en/stable/) eventloop.

```python3
from quart_trio import QuartTrio
from quart_session.redis_trio.client import RedisTrio

app = QuartTrio(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)
```

### Memcached

via `aiomcache`.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'memcached'
Session(app)
```

### MongoDB

via `motor`.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'mongodb'
app.config['SESSION_MONGODB_URI'] = 'mongodb://localhost:27017/my_database'
app.config['SESSION_MONGODB_COLLECTION'] = 'sessions'
Session(app)
```

### JSON serializer

[flask-session](https://pypi.org/project/Flask-Session/) uses `pickle`
for session data while Quart-Session uses [a JSON serializer](https://gitlab.com/pgjones/quart/blob/37e249b9b146824a8668eaa1daa12392aeb00256/src/quart/json/tag.py#L141)
capable of serializing the usual JSON types, as well as: `Tuple`, `Bytes`,
`Markup`, `UUID`, and `DateTime`.

JSON as session data allows for greater interoperability with other
programs/languages that might want to read session data straight
from a back-end.

If ~~for some unholy reason~~ you prefer `pickle` or your own serializer,

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)

try:
    import cPickle as pickle
except ImportError:
    import pickle

app.session_interface.serialize = pickle
```

### Back-end usage

At any point you may interface with the session back-end directly:

```python3
from quart_session.sessions import SessionInterface

@app.route("/")
async def hello():
    cache: SessionInterface = app.session_interface
    await cache.set("random_key", "val", expiry=3600)
    data = await cache.get("random_key")
```

The interface will have the `get`, `set`, and `delete` methods available (regardless of
back-end - similar to how [aiocache](https://github.com/argaen/aiocache) works).

### Performance

[flask-session](https://pypi.org/project/Flask-Session/) sets a
session for each incoming request, including static files. From experience,
this often puts unneeded load on underlying session infrastructure,
especially in high-traffic environments.

Quart-Session only contacts the back-end when a session changed (or created). In addition,
static file serves never emit a `Set-Cookie` header. If you'd like to enable
this though, set `SESSION_STATIC_FILE` to `True`.


### Session pinning

Associates an user's session to his/her IP address. This mitigates cookie stealing via XSS etc, and is handy
for web applications that require extra security.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PROTECTION'] = True
Session(app)
```

Session reuse from a different IP will now result in the creation of a new session, and the deletion of the old.

**Important:** If your application is behind a reverse proxy, it most
likely provides the `X-Forwarded-For` header which you **must** make use of
by explicitly setting `SESSION_REVERSE_PROXY` to `True`.

## Future development

- `FileSystemSessionInterface`
- `GoogleCloudDatastoreSessionInterface`
- Pytest

## Flask-Session

This library works very similarly to [flask-session](https://pypi.org/project/Flask-Session/).
The changes are specified below:

- Quart-Session does not emit a `Set-Cookie` on every request.
- Quart-Session does not emit a `Set-Cookie` on static file serves.
- Quart-Session uses a different serializer: `quart.json.tag.TaggedJSONSerializer` instead of `pickle`.
- Quart-Session disallows the client to supply their own made up `sid` cookie value.
- Quart-Session can do session protection.
- Quart-Session might not have all the back-end interfaces implemented (yet), such as "filesystem".

## Help

Find the Quart folk on [gitter](https://gitter.im/python-quart/lobby) or open an issue.

## License

BSD
