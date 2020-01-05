# Quart-Session

Quart-Session is an extension for Quart that adds support for
server-side sessions to your application.

Based on [flask-session](https://pypi.org/project/Flask-Session/).

## Quick start

Quart-Session can be installed via pipenv or
pip,

```bash
$ pipenv install quart-session
$ pip install quart-session
```

and requires Python 3.7.0 or higher. A fairly minimal Quart-Session example is,

```python3
from quart import Quart, session
from quart_session import Session

app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)

@app.route('/')
async def hello():
    session["foo"] = "bar"
    return 'hello'

app.run()
```

## Features


### Redis support

via `aioredis`.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)
```

If you already have a `aioredis.Client` instance and you'd like to share
it with the session interface,

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'

@app.before_serving
async def setup():
    cache = await aioredis.create_redis_pool(...)
    app.config['SESSION_REDIS'] = cache
    Session(app)
```

By default, Quart-session creates a single connection to Redis, while
the example above sets up a connection pool.

#### Trio support

Quart-Session comes with [an (experimental) Redis client](quart_session/redis_trio) for use with the [Trio](https://trio.readthedocs.io/en/stable/) eventloop.

```python3
from quart_trio import QuartTrio
from quart_session.redis_trio.client import RedisTrio

app = QuartTrio(__name__)
app.config['SESSION_TYPE'] = 'redis'
Session(app)
```

### Memcached support

via `aiomcache`.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'memcached'
Session(app)
```

### JSON serializer

[flask-session](https://pypi.org/project/Flask-Session/) uses `pickle`
for session data, Quart-Session opts for a JSON serializer capable of
(de)serializing the usual JSON types, as well as: `Tuple`, `Bytes`,
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

### Session control

By default, [flask-session](https://pypi.org/project/Flask-Session/) sets a
session for each incoming request, including static files. From experience,
this approach can put unneeded load on underlying session infrastructure,
especially in high-traffic environments.

Quart-Session offers control over the session creation. For example, often you'll only need to create a session when
a user successfully logs in.

To enable this behaviour, set `SESSION_EXPLICIT` to `True`.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_EXPLICIT'] = True
Session(app)

@app.route('/')
async def root():
    if session.get('authenticated'):
        return "Welcome back!"
    return "Welcome anonymous!"

@app.route('/login')
async def login():
    session["authenticated"] = True
    session.dirty()  # mark session for saving
    return 'Logged in!'

app.run()
```

To re-gain the old behaviour of always emitting a `Set-Cookie` header on static file serves,
set `SESSION_STATIC_FILE` to `True`.


### Session pinning

Associates an user's session to his/her IP address. This mitigates cookie stealing via XSS etc, and is handy
for paranoid web applications.

```python3
app = Quart(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_HIJACK_PROTECTION'] = True
Session(app)
```

Session reuse from a different IP will now result in the creation of a new session, and the deletion of the old.

**Important:** If your application is behind a reverse proxy, it most
likely provides the `X-Forwarded-For` header which you **must** make use of
by explicitly setting `SESSION_HIJACK_REVERSE_PROXY` to `True`.

## Future development

The following session interfaces would be nice to have:

- `MongoDBSessionInterface`
- `FileSystemSessionInterface`
- `GoogleCloudDatastoreSessionInterface`

Other to-do's:

- Unit testing
- Documentation (Sphinx)

## Migrating from Flask

This library works very similarly to [flask-session](https://pypi.org/project/Flask-Session/).
The `quart_session.sessions` APIs are not 100% the same, but unless you
are embedded in Flask-Session's internals, a migration should be fairly
straightforward. The distinct changes are specified below:

- Quart-Session does not `Set-Cookie` on (static) files by default.
- Quart-Session might not have all the back-end interfaces implemented (yet), such as "filesystem".
- Quart-Session uses a different serializer: `quart.json.tag.TaggedJSONSerializer` instead of `pickle`.
- Quart-Session disallows the client to supply their own made up `sid` cookie value.

## Help

Find the Quart folk on [gitter](https://gitter.im/python-quart/lobby) or open an issue.

## License

BSD