### 1.0.3 2021-08-31

- Migrated to aioredis 2
- SameSite support https://github.com/sanderfoobar/quart-session/commit/8daae3a6734e8f7da13954d5a1a5da8f5fc5a49a
- Memcached stuff https://github.com/filak/quart-session/commit/004871c495a069784e57e604b69f65af1b7e645a

### 1.0.0 2020-01-15

- Added support for arbitrary usage of caching backends.
    - Exposed `get`, `set`, `delete` on the session interface for direct usage.
- Renamed `SESSION_HIJACK_REVERSE_PROXY` to `SESSION_REVERSE_PROXY`.
- Renamed `SESSION_HIJACK_PROTECTION` to `SESSION_PROTECTION`.
- Removed fallback when `X-Forwarded-For` is not present whilst USING `SESSION_REVERSE_PROXY`, emit error instead.
- Fixed a bug where session timeouts would default to 600 seconds.
- Deprecated/disabled the `dirty()` method.

### 0.0.1 2020-01-04

- Released initial pre alpha version.
