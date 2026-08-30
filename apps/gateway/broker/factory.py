"""Pick the broker from config, and say loudly when it is not a real one."""

from __future__ import annotations

import logging

from ..config import Config
from .base import Broker, Containment, NotWiredBroker
from .conversion import AssetGraph

log = logging.getLogger("ev.broker")

MOCK_BANNER = (
    "=" * 68
    + "\n  broker.transport = %s -- NO ORDER REACHES ANY BROKER.\n"
      "  Quotes, fills and P/L are synthetic. Nothing here is evidence that\n"
      "  the cTrader link works; that needs the phase 2 acceptance run.\n"
    + "=" * 68
)


def build_broker(
    cfg: Config,
    *,
    containment: Containment | None = None,
    graph: AssetGraph | None = None,
    env: dict[str, str] | None = None,
) -> Broker:
    if cfg.broker.transport == "none":
        log.warning(MOCK_BANNER, "none")
        return NotWiredBroker(containment)

    from .ctrader import CTraderBroker

    if cfg.broker.transport == "mock":
        from .mock import MockTransport

        log.warning(MOCK_BANNER, "mock")
        transport = MockTransport()
        env = dict(env or {})
        # The mock authenticates against itself, so the operator does not need
        # credentials to run it. Anything the real transport needs is still
        # required by check_secrets.
        env.setdefault(cfg.broker.client_id_env, "mock-client-id")
        env.setdefault(cfg.broker.client_secret_env, "mock-client-secret")
        env.setdefault(cfg.broker.token_env, transport.state.access_token)
        env.setdefault(cfg.broker.refresh_env, transport.state.refresh_token)
        env.setdefault(cfg.broker.account_id_env, str(transport.state.account_id))
        return CTraderBroker(cfg, transport, containment=containment, graph=graph, env=env)

    from .transport import TwistedTransport

    return CTraderBroker(
        cfg,
        TwistedTransport(cfg.broker.host, cfg.broker.port),
        containment=containment,
        graph=graph,
        env=env,
    )
