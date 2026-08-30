"""The seam between the broker logic and the wire.

``CTraderBroker`` builds and reads real ``ProtoOA*`` messages either way. Only
*delivery* differs: :class:`TwistedTransport` puts them on a TLS socket to
Spotware, :class:`~apps.gateway.broker.mock.MockTransport` answers them in
process. That is deliberate -- a mock that stubbed the broker interface instead
would leave symbol mapping, volume conversion, and execution-event translation
completely untested, which is exactly the code most likely to be wrong.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

log = logging.getLogger("ev.broker.transport")

#: Called with each unsolicited inbound message (spots, execution events that
#: are not a reply, heartbeats).
MessageSink = Callable[[Any], None]


class TransportError(RuntimeError):
    pass


@runtime_checkable
class Transport(Protocol):
    connected: bool

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    async def request(
        self, message: Any, *, client_msg_id: str | None = None, timeout: float = 10.0
    ) -> Any:
        """Send and await the matching reply, already unwrapped from its
        envelope."""
        ...

    def send_nowait(self, message: Any, *, client_msg_id: str | None = None) -> None:
        """Fire and forget. Used for heartbeats, where a reply is not expected
        and a pending deferred per beat would leak."""
        ...

    def set_message_sink(self, sink: MessageSink) -> None: ...


class TwistedTransport:
    """Wraps ``ctrader_open_api.Client`` and bridges its Deferreds to asyncio.

    Safe only because ``reactor_setup.install()`` put Twisted on the asyncio
    reactor, so ``Deferred.asFuture`` resolves on the loop the gateway is
    already running. Without that, awaiting one of these would hang forever
    while the broker socket looked perfectly healthy.
    """

    def __init__(self, host: str, port: int) -> None:
        from ctrader_open_api import Client, Protobuf, TcpProtocol

        self._protobuf = Protobuf
        self.host = host
        self.port = port
        self.connected = False
        self._sink: MessageSink | None = None
        self._client = Client(host, port, TcpProtocol)
        self._client.setConnectedCallback(self._on_connected)
        self._client.setDisconnectedCallback(self._on_disconnected)
        self._client.setMessageReceivedCallback(self._on_message)
        self._ready: asyncio.Future[None] | None = None

    # -- lifecycle ----------------------------------------------------------

    async def connect(self, timeout: float = 20.0) -> None:
        loop = asyncio.get_running_loop()
        self._ready = loop.create_future()
        self._client.startService()
        try:
            await asyncio.wait_for(asyncio.shield(self._ready), timeout)
        except asyncio.TimeoutError:
            raise TransportError(
                f"no connection to {self.host}:{self.port} within {timeout}s"
            ) from None

    async def disconnect(self) -> None:
        self._client.stopService()
        self.connected = False

    def _on_connected(self, client: Any) -> None:
        self.connected = True
        if self._ready is not None and not self._ready.done():
            self._ready.set_result(None)

    def _on_disconnected(self, client: Any, reason: Any) -> None:
        self.connected = False
        log.warning("broker socket down: %s", reason)

    def _on_message(self, client: Any, message: Any) -> None:
        if self._sink is None:
            return
        try:
            self._sink(self._protobuf.extract(message))
        except Exception:
            # Containment lives in the broker; a transport that raised here
            # would take the reactor down with it.
            log.exception("message sink raised")

    # -- io -----------------------------------------------------------------

    async def request(
        self, message: Any, *, client_msg_id: str | None = None, timeout: float = 10.0
    ) -> Any:
        deferred = self._client.send(
            message, clientMsgId=client_msg_id, responseTimeoutInSeconds=timeout
        )
        raw = await deferred.asFuture(asyncio.get_running_loop())
        return self._protobuf.extract(raw)

    def send_nowait(self, message: Any, *, client_msg_id: str | None = None) -> None:
        deferred = self._client.send(message, clientMsgId=client_msg_id)
        deferred.addErrback(lambda failure: log.debug("nowait send failed: %s", failure))

    def set_message_sink(self, sink: MessageSink) -> None:
        self._sink = sink
