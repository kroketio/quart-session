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