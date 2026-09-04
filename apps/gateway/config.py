"""Config loader and boot-fails.

Every rule in here is a structural guarantee, not a preference: the gateway refuses to start
rather than run in a shape where a live account, a cloud STT path, a tilt-gated close, or a
mis-weighted score is reachable. A boot-fail is loud and non-zero on purpose — a half-started
gateway is worse than one that never opened the socket.
"""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

LIVE_HOSTS = frozenset({"live.ctraderapi.com"})

# Trading actions live on these pad controls; voice may never be bound to one of them.
RESERVED_PAD_BUTTONS = frozenset({"LT", "RT", "A", "B", "X", "Y"})

# Secrets that must exist before the gateway is allowed to open anything.
REQUIRED_ENV = ("CT_CLIENT_ID", "CT_CLIENT_SECRET", "CT_ACCESS_TOKEN", "CT_REFRESH_TOKEN",
                "CT_ACCOUNT_ID", "EV_WS_TOKEN")

SCORE_WEIGHT_TOLERANCE = 1e-9

# The provider caps its web-search domain filter at five entries.
MAX_ALLOWED_DOMAINS = 5


class ConfigError(ValueError):
    """A configuration the gateway refuses to run. Always fatal, never a warning."""


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BrokerConfig(Base):
    """cTrader Open API is the only adapter in v1; there is no paper matcher and no MT5."""

    adapter: Literal["ctrader"]
    host: str
    port: int = Field(gt=0, lt=65536)
    proto: Literal["protobuf"] = "protobuf"
    account_id_env: str = "CT_ACCOUNT_ID"
    token_env: str = "CT_ACCESS_TOKEN"
    refresh_env: str = "CT_REFRESH_TOKEN"
    client_id_env: str = "CT_CLIENT_ID"
    client_secret_env: str = "CT_CLIENT_SECRET"

    @field_validator("host")
    @classmethod
    def _refuse_live_host(cls, v: str) -> str:
        if v.strip().lower() in LIVE_HOSTS:
            raise ValueError(f"broker.host `{v}` is the live endpoint; v1 is demo-only")
        return v


class SymbolConfig(Base):
    name: str
    max_spread: float | None = Field(default=None, gt=0)
    max_lots: float = Field(gt=0)
    default_lots: float = Field(gt=0)
    lot_step: float = Field(gt=0)

    @model_validator(mode="after")
    def _default_within_cap(self) -> SymbolConfig:
        if self.default_lots > self.max_lots:
            raise ValueError(
                f"{self.name}: default_lots {self.default_lots} exceeds max_lots {self.max_lots}"
            )
        return self


class SessionConfig(Base):
    days: list[Literal["sun", "mon", "tue", "wed", "thu", "fri", "sat"]]
    start: str
    end: str


class RiskConfig(Base):
    max_positions: int = Field(gt=0)
    max_daily_loss_usd: float = Field(gt=0)
    min_seconds_between_orders: float = Field(ge=0)
    panic_flatten_on_disconnect: bool = False
    r_unit_usd: float = Field(gt=0, description="R when a fire carries no stop; see phase 2")
    default_stop: dict[str, float] = Field(default_factory=dict, description="Per-symbol, price units")


class GatewayConfig(Base):
    listen: str
    static_dir: str
    ws_path: str = "/ws"
    # Browser Origin of the HUD (the page that opens /ws), not the gateway hostname.
    # Split deploy: HUD at e.g. https://bobvolman.com, gateway at https://gw.bobvolman.com.
    public_origin: str
    # Extra HUD origins allowed to open /ws and call /api (CORS). public_origin is always included.
    cors_origins: list[str] = Field(default_factory=list)
    token_env: str = "EV_WS_TOKEN"
    heartbeat_s: float = Field(gt=0)
    heartbeat_dead_s: float = Field(gt=0)
    max_frame_bytes: int = Field(gt=0)

    @property
    def host(self) -> str:
        return self.listen.rsplit(":", 1)[0]

    @property
    def port(self) -> int:
        return int(self.listen.rsplit(":", 1)[1])

    @property
    def allowed_origins(self) -> tuple[str, ...]:
        """HUD origins allowed to talk to this gateway (CORS + WebSocket Origin)."""
        seen: list[str] = []
        for item in (self.public_origin, *self.cors_origins):
            cleaned = item.rstrip("/")
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
        return tuple(seen)

    @model_validator(mode="after")
    def _dead_after_beat(self) -> GatewayConfig:
        if self.heartbeat_dead_s <= self.heartbeat_s:
            raise ValueError("gateway.heartbeat_dead_s must exceed heartbeat_s")
        return self


class UiConfig(Base):
    theme: Literal["dark"] = "dark"
    desktop_only: bool = True


class SttConfig(Base):
    """`mode` has exactly two values. There is no cloud path to misconfigure into existence."""

    mode: Literal["local", "off"]
    model: str = "small.en"
    lang: str = "en"


class VoiceConfig(Base):
    enabled: bool = True
    stt: SttConfig
    bindings: list[str]
    hold_stream: bool = True
    max_seconds: int = Field(gt=0)
    max_bytes: int = Field(gt=0)
    max_uploads_per_hour: int = Field(gt=0)
    stt_timeout_s: float = Field(gt=0)
    audio_retention_days: int = Field(ge=0)
    tts: Literal["off", "browser"] = "off"

    @field_validator("tts", mode="before")
    @classmethod
    def _yaml_off_is_a_string(cls, v: Any) -> Any:
        """YAML 1.1 reads a bare `off` as boolean false. Accept it; it means the same thing."""
        return "off" if v is False else v

    @field_validator("bindings")
    @classmethod
    def _no_trading_buttons(cls, v: list[str]) -> list[str]:
        for binding in v:
            for part in binding.replace("+", " ").split():
                if part.strip().upper() in RESERVED_PAD_BUTTONS:
                    raise ValueError(
                        f"voice.bindings `{binding}` resolves to trading control `{part}`; "
                        "voice may never share the order path"
                    )
        return v


class TapeConfig(Base):
    dt_s: float = Field(gt=0)
    ring_minutes: int = Field(gt=0)
    pre_roll_s: int = Field(ge=0)
    post_roll_s: int = Field(ge=0)
    retention_days: int = Field(ge=0)


class TiltConfig(Base):
    enabled: bool = True
    gate_close: bool = False
    warm: float = Field(ge=0, le=1)
    hot: float = Field(ge=0, le=1)
    scorched: float = Field(ge=0, le=1)
    confirm_hold_ms: int = Field(ge=0)
    cooldown_s: int = Field(ge=0)

    @model_validator(mode="after")
    def _never_gate_a_close(self) -> TiltConfig:
        if self.gate_close:
            raise ValueError("tilt.gate_close: true — tilt may never gate a close or a panic")
        if not self.warm < self.hot < self.scorched:
            raise ValueError("tilt bands must ascend: warm < hot < scorched")
        return self


class ScoreConfig(Base):
    trades_max: int = Field(gt=0)
    band_width: float = Field(gt=0)
    decline_credit_max: int = Field(ge=0)
    weights: dict[str, float]

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> ScoreConfig:
        total = sum(self.weights.values())
        if abs(total - 1.0) > SCORE_WEIGHT_TOLERANCE:
            raise ValueError(
                f"score.weights sum to {total}, not 1.0; the score would be silently mis-weighted"
            )
        return self


class DeckConfig(Base):
    """~20 sessions a month means the first two months of Sharpe are noise."""

    min_sessions_for_sharpe: int = Field(default=30, ge=2)


class PlaybookConfig(Base):
    seed_volman: bool = True
    allow_custom: bool = True


class CopilotConfig(Base):
    """The desk is advisory. `on_hot_path: true` is not a mode — it is a boot-fail."""

    enabled: bool = True
    on_hot_path: bool = False
    model: str = ""
    allowed_domains: list[str] = Field(default_factory=list)

    @field_validator("allowed_domains")
    @classmethod
    def _provider_caps_the_filter(cls, v: list[str]) -> list[str]:
        if len(v) > MAX_ALLOWED_DOMAINS:
            raise ValueError(
                f"copilot.allowed_domains has {len(v)} entries; the provider caps the search "
                f"filter at {MAX_ALLOWED_DOMAINS}"
            )
        return v

    @model_validator(mode="after")
    def _never_on_hot_path(self) -> CopilotConfig:
        if self.on_hot_path:
            raise ValueError("copilot.on_hot_path: true — the desk may never sit on the order path")
        return self


class CalendarSignalConfig(Base):
    source: Literal["ff_weekly", "off"] = "ff_weekly"
    min_impact: Literal["Low", "Medium", "High"] = "High"


class SignalsConfig(Base):
    """Trusted signal sources. An empty `x_accounts` means x_search is never enabled at all."""

    calendar: CalendarSignalConfig = Field(default_factory=CalendarSignalConfig)
    x_accounts: list[str] = Field(default_factory=list)


class TradingViewConfig(Base):
    enabled: bool = False
    auto_trade: bool = False
    webhook_secret_env: str = "TV_WEBHOOK_SECRET"

    @model_validator(mode="after")
    def _never_auto_trade(self) -> TradingViewConfig:
        if self.auto_trade:
            raise ValueError("tradingview.auto_trade: true — a webhook may never place an order")
        return self


class PathsConfig(Base):
    """Everything durable lives under one volume, so backup and restore have one root."""

    data_dir: str = "/data"

    @property
    def data_dir_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def db(self) -> Path:
        return Path(self.data_dir) / "journal.db"

    @property
    def voice_dir(self) -> Path:
        return Path(self.data_dir) / "voice"

    @property
    def models_dir(self) -> Path:
        return Path(self.data_dir) / "models"

    @property
    def secure_dir(self) -> Path:
        """Refreshed cTrader tokens land here, mode 0600, never in git or a backup archive."""
        return Path(self.data_dir) / "secure"


class AppConfig(Base):
    mode: Literal["demo"]
    timezone: str
    paths: PathsConfig = Field(default_factory=PathsConfig)
    broker: BrokerConfig
    symbols: list[SymbolConfig] = Field(min_length=1)
    session: SessionConfig
    risk: RiskConfig
    gateway: GatewayConfig
    ui: UiConfig = Field(default_factory=UiConfig)
    voice: VoiceConfig
    tape: TapeConfig
    tilt: TiltConfig
    score: ScoreConfig
    deck: DeckConfig = Field(default_factory=DeckConfig)
    playbook: PlaybookConfig
    copilot: CopilotConfig = Field(default_factory=CopilotConfig)
    signals: SignalsConfig = Field(default_factory=SignalsConfig)
    tradingview: TradingViewConfig = Field(default_factory=TradingViewConfig)

    @field_validator("timezone")
    @classmethod
    def _iana_only(cls, v: str) -> str:
        if v.strip().lower() == "local":
            raise ValueError(
                "timezone: local — an evening session needs a named IANA zone, not the host's guess"
            )
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"timezone `{v}` is not a known IANA zone") from exc
        return v

    @model_validator(mode="after")
    def _frame_cap_matches_protocol(self) -> AppConfig:
        from protocol import MAX_FRAME_BYTES

        if self.gateway.max_frame_bytes != MAX_FRAME_BYTES:
            raise ValueError(
                f"gateway.max_frame_bytes {self.gateway.max_frame_bytes} disagrees with "
                f"protocol v1's {MAX_FRAME_BYTES}"
            )
        return self

    @model_validator(mode="after")
    def _default_stop_covers_symbols(self) -> AppConfig:
        missing = [s.name for s in self.symbols if s.name not in self.risk.default_stop]
        if missing:
            raise ValueError(
                f"risk.default_stop is missing {', '.join(missing)}; R would be undefined for them"
            )
        return self


def _check_bind(cfg: AppConfig, *, dev: bool, container: bool) -> None:
    """A public bind is only allowed where something else is keeping the port off the WAN.

    Two cases qualify. `EV_DEV=1` is a developer's own machine. `EV_CONTAINER_BIND=1` is the
    deploy shape: Docker can only forward a published port to a process bound on the container's
    own `0.0.0.0`, so the loopback guarantee moves out to the port publishing
    (`127.0.0.1:8444:8444`) and the host firewall. Without one of those flags, loopback here is
    the only thing standing between the order socket and the internet.
    """
    if dev or container:
        return
    host = cfg.gateway.host
    try:
        addr = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ConfigError(f"gateway.listen host `{host}` is not an IP address") from exc
    if not addr.is_loopback:
        raise ConfigError(
            f"gateway.listen `{cfg.gateway.listen}` is not loopback; "
            "set EV_DEV=1 to allow it in development"
        )


def hud_origins(cfg: AppConfig, env: dict[str, str] | None = None) -> list[str]:
    """Origins the browser may send when talking to this gateway.

    `gateway.public_origin` plus `gateway.cors_origins`, and when `EV_DEV=1` also the
    Vite dev server so `npm run dev` can open a remote or local gateway without editing YAML.
    """
    env = dict(os.environ) if env is None else env
    origins = list(cfg.gateway.allowed_origins)
    if env.get("EV_DEV") == "1":
        for extra in ("http://localhost:5173", "http://127.0.0.1:5173"):
            if extra not in origins:
                origins.append(extra)
    return origins


def _check_secrets(cfg: AppConfig, env: dict[str, str]) -> None:
    """Refuse to half-start on missing credentials; point at the README instead."""
    names = [cfg.broker.client_id_env, cfg.broker.client_secret_env, cfg.broker.token_env,
             cfg.broker.refresh_env, cfg.broker.account_id_env, cfg.gateway.token_env]
    missing = [n for n in names if not env.get(n)]
    if missing:
        raise ConfigError(
            f"missing required env: {', '.join(missing)} — "
            "see README 'cTrader credentials (one-time, manual)'"
        )
    if cfg.tradingview.enabled and not env.get(cfg.tradingview.webhook_secret_env):
        raise ConfigError(f"tradingview.enabled but {cfg.tradingview.webhook_secret_env} is unset")


def load_config(
    path: str | Path,
    *,
    env: dict[str, str] | None = None,
    check_secrets: bool = True,
) -> AppConfig:
    """Read, validate, and boot-check a config file. Raises `ConfigError` on anything unsafe."""
    env = dict(os.environ) if env is None else env
    path = Path(path)
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"config is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"config must be a mapping, got {type(raw).__name__}")

    # Deploy and a dev checkout override these without editing the file: listen bind
    # (see `_check_bind`), durable volume, and the HUD origin allowlist for CORS / WS.
    listen_override = env.get("EV_LISTEN")
    if listen_override:
        gateway = raw.get("gateway")
        if not isinstance(gateway, dict):
            raise ConfigError("EV_LISTEN set but config has no `gateway` block to override")
        gateway["listen"] = listen_override

    public_override = (env.get("EV_PUBLIC_ORIGIN") or "").strip()
    if public_override:
        gateway = raw.get("gateway")
        if not isinstance(gateway, dict):
            raise ConfigError("EV_PUBLIC_ORIGIN set but config has no `gateway` block to override")
        gateway["public_origin"] = public_override

    cors_override = (env.get("EV_CORS_ORIGINS") or "").strip()
    if cors_override:
        gateway = raw.get("gateway")
        if not isinstance(gateway, dict):
            raise ConfigError("EV_CORS_ORIGINS set but config has no `gateway` block to override")
        extra = [item.strip() for item in cors_override.split(",") if item.strip()]
        gateway["cors_origins"] = extra

    data_dir_override = env.get("EV_DATA_DIR")
    if data_dir_override:
        raw.setdefault("paths", {})["data_dir"] = data_dir_override

    try:
        cfg = AppConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"invalid config {path}:\n{exc}") from exc

    _check_bind(cfg, dev=env.get("EV_DEV") == "1", container=env.get("EV_CONTAINER_BIND") == "1")
    if check_secrets:
        _check_secrets(cfg, env)
    return cfg
