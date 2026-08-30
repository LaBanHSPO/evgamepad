"""Config load + the boot-fails that carry the product's safety invariants.

These are not conventions or runtime checks. A config that could put real money,
the AI, the voice channel, or the score on the order path makes the process
refuse to start, which is why they live in one function that runs before
anything opens a socket.
"""

from __future__ import annotations

import os
import zoneinfo
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Any of these in ``broker.host`` means real money. Substring match, so a
#: creative subdomain does not slip through an equality test.
LIVE_HOST_MARKERS = ("live.ctraderapi.com", "live-", ".live.")

#: Voice may never resolve to a control that navigates or fires.
FORBIDDEN_VOICE_BINDINGS = {"LT", "RT", "A", "B", "X", "Y"}

REQUIRED_SECRET_ENVS = (
    "CT_CLIENT_ID",
    "CT_CLIENT_SECRET",
    "CT_ACCESS_TOKEN",
    "CT_REFRESH_TOKEN",
    "CT_ACCOUNT_ID",
    "EV_WS_TOKEN",
)

DEFAULT_CONFIG_PATH = Path("config/default.yaml")


class BootFail(SystemExit):
    """Exit non-zero with a named invariant. Never catch this."""

    def __init__(self, invariant: str, detail: str) -> None:
        super().__init__(f"BOOT-FAIL [{invariant}] {detail}")
        self.invariant = invariant
        self.detail = detail


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BrokerCfg(Base):
    adapter: Literal["ctrader"] = "ctrader"
    #: How ProtoOA messages are delivered. ``real`` opens a TLS socket to
    #: Spotware. ``mock`` answers them in process (see broker/mock.py) so the
    #: gateway can be exercised without credentials -- it is never a substitute
    #: for the acceptance run against a real demo account. ``none`` is the
    #: phase 1 stub that refuses every broker-changing call.
    transport: Literal["real", "mock", "none"] = "real"
    host: str = "demo.ctraderapi.com"
    port: int = 5035
    proto: Literal["protobuf"] = "protobuf"
    account_id_env: str = "CT_ACCOUNT_ID"
    token_env: str = "CT_ACCESS_TOKEN"
    refresh_env: str = "CT_REFRESH_TOKEN"
    client_id_env: str = "CT_CLIENT_ID"
    client_secret_env: str = "CT_CLIENT_SECRET"


class SymbolCfg(Base):
    name: str
    max_lots: float = Field(gt=0)
    default_lots: float = Field(gt=0)
    lot_step: float = Field(gt=0)
    max_spread: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _default_within_max(self) -> SymbolCfg:
        if self.default_lots > self.max_lots:
            raise ValueError(f"{self.name}: default_lots exceeds max_lots")
        return self


class SessionCfg(Base):
    days: list[Literal["sun", "mon", "tue", "wed", "thu", "fri", "sat"]]
    start: str = "18:00"
    end: str = "23:30"


class RiskCfg(Base):
    max_positions: int = Field(default=1, ge=1)
    max_daily_loss_usd: float = Field(default=200.0, gt=0)
    min_seconds_between_orders: float = Field(default=2.0, ge=0)
    panic_flatten_on_disconnect: bool = False
    r_unit_usd: float = Field(default=20.0, gt=0)
    default_stop: dict[str, float] = Field(default_factory=dict)


class GatewayCfg(Base):
    listen: str = "127.0.0.1:8444"
    static_dir: str = "app/dist"
    ws_path: str = "/ws"
    public_origin: str = "https://YOUR_DOMAIN"
    token_env: str = "EV_WS_TOKEN"
    heartbeat_s: float = 1.0
    heartbeat_dead_s: float = 3.0
    max_frame_bytes: int = 65536

    @property
    def host(self) -> str:
        return self.listen.rsplit(":", 1)[0]

    @property
    def port(self) -> int:
        return int(self.listen.rsplit(":", 1)[1])


class UiCfg(Base):
    theme: Literal["dark"] = "dark"
    desktop_only: bool = True


class SttCfg(Base):
    #: ``local`` or ``off``. There is no cloud code path to misconfigure into.
    mode: str = "local"
    model: str = "small.en"
    lang: str = "en"


class VoiceCfg(Base):
    enabled: bool = True
    stt: SttCfg = Field(default_factory=SttCfg)
    bindings: list[str] = Field(default_factory=lambda: ["LB+RB", "key:V"])
    hold_stream: bool = True
    max_seconds: int = 60
    max_bytes: int = 262144
    max_uploads_per_hour: int = 60
    stt_timeout_s: int = 60
    audio_retention_days: int = 365
    tts: Literal["off", "browser"] = "off"

    @model_validator(mode="before")
    @classmethod
    def _yaml_off_is_a_bool(cls, data: Any) -> Any:
        # YAML 1.1 reads a bare `off` as False. Coerce rather than boot-fail on
        # a config that says exactly what it means.
        if isinstance(data, dict) and data.get("tts") is False:
            data = {**data, "tts": "off"}
        return data


class TapeCfg(Base):
    dt_s: int = Field(default=1, ge=1)
    ring_minutes: int = Field(default=90, ge=1)
    pre_roll_s: int = Field(default=300, ge=0)
    post_roll_s: int = Field(default=300, ge=0)
    retention_days: int = 730

    @model_validator(mode="after")
    def _ring_covers_rolls(self) -> TapeCfg:
        if self.ring_minutes * 60 < self.pre_roll_s:
            raise ValueError("tape.ring_minutes cannot hold tape.pre_roll_s")
        return self


class TiltCfg(Base):
    enabled: bool = True
    #: Structurally false. Tilt adds friction to opens; a close or a panic is a
    #: safety exit and is never gated.
    gate_close: bool = False
    warm: float = 0.35
    hot: float = 0.60
    scorched: float = 0.80
    confirm_hold_ms: int = 750
    cooldown_s: int = 300

    @model_validator(mode="after")
    def _bands_ascend(self) -> TiltCfg:
        if not 0 < self.warm < self.hot < self.scorched <= 1.0:
            raise ValueError("tilt bands must ascend within (0, 1]")
        return self


class ScoreCfg(Base):
    trades_max: int = 6
    band_width: int = 1
    decline_credit_max: int = 15
    weights: dict[str, float] = Field(default_factory=dict)


class PlaybookCfg(Base):
    seed_volman: bool = True
    allow_custom: bool = True


class CopilotCfg(Base):
    enabled: bool = True
    #: Structurally false. The AI has no order tools and never blocks a fire.
    on_hot_path: bool = False
    model: str = "grok-4"
    api_key_env: str = "XAI_API_KEY"
    min_interval_s: float = 1.0
    max_interval_s: float = 30.0


class TradingViewCfg(Base):
    enabled: bool = False
    #: Structurally false. Signals become ``signal.item`` and nothing else.
    auto_trade: bool = False
    secret_env: str = "TV_WEBHOOK_SECRET"


class Config(Base):
    mode: Literal["demo", "live"] = "demo"
    timezone: str = "Asia/Ho_Chi_Minh"
    dev: bool = False
    db_path: str = "var/ev.sqlite3"
    broker: BrokerCfg = Field(default_factory=BrokerCfg)
    symbols: list[SymbolCfg] = Field(default_factory=list)
    session: SessionCfg
    risk: RiskCfg = Field(default_factory=RiskCfg)
    gateway: GatewayCfg = Field(default_factory=GatewayCfg)
    ui: UiCfg = Field(default_factory=UiCfg)
    voice: VoiceCfg = Field(default_factory=VoiceCfg)
    tape: TapeCfg = Field(default_factory=TapeCfg)
    tilt: TiltCfg = Field(default_factory=TiltCfg)
    score: ScoreCfg = Field(default_factory=ScoreCfg)
    playbook: PlaybookCfg = Field(default_factory=PlaybookCfg)
    copilot: CopilotCfg = Field(default_factory=CopilotCfg)
    tradingview: TradingViewCfg = Field(default_factory=TradingViewCfg)

    def symbol(self, name: str) -> SymbolCfg | None:
        return next((s for s in self.symbols if s.name == name), None)

    @property
    def symbol_names(self) -> list[str]:
        return [s.name for s in self.symbols]


Annotated  # re-exported implicitly by pydantic; keeps the import honest


def check_invariants(cfg: Config) -> None:
    """Every boot-fail, in one place. Raises :class:`BootFail`, never returns a
    warning -- a half-started gateway is the failure mode this prevents."""

    if cfg.mode != "demo":
        raise BootFail("live_mode", f"mode is {cfg.mode!r}; only 'demo' exists")

    host = cfg.broker.host.lower()
    if any(marker in host for marker in LIVE_HOST_MARKERS):
        raise BootFail("live_host", f"broker.host {cfg.broker.host!r} is a live endpoint")

    if cfg.broker.adapter != "ctrader":
        raise BootFail("broker_adapter", f"{cfg.broker.adapter!r} is not an adapter")

    tz = cfg.timezone
    if tz.lower() in {"local", "system", ""} or "/" not in tz:
        raise BootFail("timezone", f"{tz!r} is not an IANA zone")
    try:
        zoneinfo.ZoneInfo(tz)
    except Exception:
        raise BootFail("timezone", f"{tz!r} is not a known IANA zone") from None

    if not cfg.dev:
        host_part = cfg.gateway.host
        if host_part not in {"127.0.0.1", "localhost", "::1"}:
            raise BootFail(
                "public_bind",
                f"gateway.listen {cfg.gateway.listen!r} is not loopback; TLS on :443 fronts it",
            )

    if cfg.copilot.on_hot_path:
        raise BootFail("copilot_hot_path", "the AI desk has no order tools, ever")

    if cfg.tradingview.auto_trade:
        raise BootFail("tv_auto_trade", "TradingView signals are advisory only")

    if cfg.voice.stt.mode not in {"local", "off"}:
        raise BootFail(
            "stt_mode",
            f"voice.stt.mode {cfg.voice.stt.mode!r}; audio never leaves the box",
        )

    for binding in cfg.voice.bindings:
        for part in binding.replace("+", " ").split():
            if part.strip().upper() in FORBIDDEN_VOICE_BINDINGS:
                raise BootFail(
                    "voice_binding",
                    f"voice.bindings {binding!r} resolves to {part!r}; "
                    "voice is memos and ask-the-coach only",
                )

    if cfg.tilt.gate_close:
        raise BootFail("tilt_gate_close", "close and panic always execute")

    if not cfg.score.weights:
        raise BootFail("score_weights", "score.weights is empty")
    total = round(sum(cfg.score.weights.values()), 6)
    if total != 1.0:
        raise BootFail("score_weights", f"score.weights sum to {total}, not 1.0")

    if not cfg.symbols:
        raise BootFail("symbols", "no symbols configured")

    if cfg.gateway.max_frame_bytes > 65536:
        raise BootFail("max_frame", "protocol v1 caps frames at 65536 bytes")

    # A mock broker is a development tool. Reaching a real Spotware host with
    # one would mean the operator believes orders are going somewhere they are
    # not, which is the same class of mistake as pointing at a live host.
    if cfg.broker.transport != "real" and not cfg.dev:
        raise BootFail(
            "mock_transport",
            f"broker.transport is {cfg.broker.transport!r}; no order reaches a "
            "broker. Set dev: true to acknowledge this is not a real session.",
        )


def check_secrets(cfg: Config, env: dict[str, str] | None = None) -> None:
    """Refuse to start without the credentials phase 1's README says to paste.

    Kept separate from :func:`check_invariants` so tests can exercise the shape
    of a config without a populated ``.env``.
    """
    env = os.environ if env is None else env
    if cfg.broker.transport != "real":
        # A mock or stub broker has nothing to authenticate against. Requiring
        # cTrader credentials here would defeat the purpose of having one.
        names = [cfg.gateway.token_env]
    else:
        names = list(REQUIRED_SECRET_ENVS)
    if cfg.copilot.enabled:
        names.append(cfg.copilot.api_key_env)
    if cfg.tradingview.enabled:
        names.append(cfg.tradingview.secret_env)

    missing = [n for n in names if not env.get(n)]
    if missing:
        raise BootFail(
            "missing_secrets",
            f"{', '.join(missing)} unset. No auth helper ships in v1 -- "
            "run the manual consent flow in README.md and paste into .env",
        )


def load(path: str | Path = DEFAULT_CONFIG_PATH, *, secrets: bool = False) -> Config:
    """Read, validate, and enforce. The only supported way to get a Config."""
    p = Path(path)
    if not p.is_file():
        raise BootFail("config_missing", str(p))
    raw: Any = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict):
        raise BootFail("config_shape", f"{p} is not a mapping")
    try:
        cfg = Config.model_validate(raw)
    except Exception as exc:
        raise BootFail("config_invalid", str(exc).replace("\n", " ")[:400]) from None
    check_invariants(cfg)
    if secrets:
        check_secrets(cfg)
    return cfg
