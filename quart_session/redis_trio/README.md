

Code here is borrowed from [alekseyev/trio-redis](https://github.com/alekseyev/trio-redis), which was originally developed over at [Bogdanp/trio-redis](https://github.com/Bogdanp/trio-redis).

Since it has no active maintainers and no PyPI package - I am including it as-is.

## Usage

```python3
from quart_session.redis_trio import RedisTrio
cache = RedisTrio(
    addr=b"10.0.0.3", port=6379, password=b"foo")
await cache.connect()

await cache.setex(key="foo", value=42, seconds=300)
await cache.get("foo")
```

Or,

```python3
async with RedisTrio() as cache:
    await cache.set("foo", 42)
    await cache.get("foo")
```

## Future work

If someone makes a Redis+Trio client that supports connection pooling, we can switch to it.


```
:copyright: (c) 2017 by Bogdan Paul Popa.
:copyright: (c) 2019 by Oleksii Aleksieiev.
:copyright: (c) 2020 by dsc.
:license: BSD, see LICENSE for more
```
