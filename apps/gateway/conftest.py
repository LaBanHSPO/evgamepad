"""Test-session setup.

pytest imports this before any test module, which is the only place that can guarantee the
asyncio reactor is installed first. Without it, collection order decides which reactor the suite
runs on: `ctrader_open_api` does `from twisted.internet import reactor` at import time, and an
import sorter will happily place that third-party import above our own `broker.ctrader`.
"""

from __future__ import annotations

from broker.reactor_setup import install

install()
