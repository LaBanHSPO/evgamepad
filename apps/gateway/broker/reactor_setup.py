"""Install Twisted's asyncio reactor before anything imports ``reactor``.

OpenApiPy is Twisted. The gateway is asyncio. They must share one event loop, or
the failure looks like "the socket is just slow": quotes arrive in bursts,
awaits never resume, the WS heartbeat stalls while the broker link is healthy.

Twisted installs a reactor on first import and refuses to install a second, so
the ordering matters and cannot be fixed later in the process's life. Import
this module **first** -- before FastAPI, before the broker, before anything that
might transitively import ``twisted.internet.reactor``.
"""

from __future__ import annotations

import sys

INSTALLED_ATTR = "_ev_asyncio_reactor_installed"


class ReactorError(SystemExit):
    def __init__(self, detail: str) -> None:
        super().__init__(f"BOOT-FAIL [reactor] {detail}")
        self.detail = detail


def install() -> bool:
    """Install the asyncio reactor. Returns ``True`` if this call installed it,
    ``False`` if it was already correctly installed. Boot-fails on a mismatch.

    Twisted is an optional dependency (``pip install '.[broker]'``); without it
    there is no reactor to get wrong, so this is a no-op.
    """
    try:
        from twisted.internet import asyncioreactor
    except ModuleNotFoundError:
        return False

    existing = sys.modules.get("twisted.internet.reactor")
    if existing is not None:
        return verify()

    from twisted.internet import error as twisted_error

    try:
        asyncioreactor.install()
    except twisted_error.ReactorAlreadyInstalledError:
        return verify()
    return True


def verify() -> bool:
    """Confirm the installed reactor is the asyncio one. Exits non-zero with a
    named error otherwise -- a silently mismatched reactor is the single most
    likely way phase 2 fails."""
    try:
        from twisted.internet import asyncioreactor
    except ModuleNotFoundError:
        return False

    reactor = sys.modules.get("twisted.internet.reactor")
    if reactor is None:
        return False
    if not isinstance(reactor, asyncioreactor.AsyncioSelectorReactor):
        raise ReactorError(
            f"{type(reactor).__name__} was installed before the gateway could "
            "install AsyncioSelectorReactor. Import "
            "apps.gateway.broker.reactor_setup before any twisted.internet.reactor "
            "import."
        )
    return False
