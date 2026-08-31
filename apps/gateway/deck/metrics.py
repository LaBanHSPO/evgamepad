"""Deck metrics: pure functions over journal rows.

No LLM computes a number that reaches this deck. The copilot may narrate what these functions
produced; it cannot produce one itself.

Two ideas from Steenbarger's work shape what is measured here, and they are cited rather than
reproduced: trading is a *performance* activity, so the process is the thing to score; and
markets do not offer equal opportunity every night, so a flat evening on a dead tape is a good
evening and the numbers have to be able to say so.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from risk.rules import OPEN_RULES

CITATION = (
    "Process framing after Brett Steenbarger, *The Daily Trading Coach*, *Trading Psychology 2.0*, "
    "and *Enhancing Trader Performance*. Read the books; the metrics here are our own."
)

DISCLAIMER = "cTrader demo · entertainment, not advice"

# Evenings per year, for annualising a per-session Sharpe. ~20 a month.
SESSIONS_PER_YEAR = 240

# Below this many sessions a Sharpe is noise, and the deck says so instead of printing one.
DEFAULT_MIN_SESSIONS_FOR_SHARPE = 30

RuleOrigin = Literal["gateway", "process"]

# Rules the gateway actually enforced *and* that a journal row can reconstruct. Imported by id
# from phase 2 rather than re-listed, so the deck cannot drift from what the gate did.
_GATEWAY_RULE_IDS = {"session_window", "max_lots", "max_positions"}
GATEWAY_ADHERENCE_RULES = tuple(r.id for r in OPEN_RULES if r.id in _GATEWAY_RULE_IDS)

# Process expectations the gateway never enforced. Kept separate and labelled, so the deck never
# claims a fire "broke a rule" the gateway allowed.
PROCESS_ADHERENCE_RULES = ("named_setup", "event_guard")

ADHERENCE_RULES = GATEWAY_ADHERENCE_RULES + PROCESS_ADHERENCE_RULES


@dataclass(frozen=True)
class Fire:
    """One fire, as the deck sees it. Assembled from `trade_plan` plus `trade_closed`."""

    cid: str
    session_id: str
    symbol: str
    setup_tag: str | None
    lots: float
    max_lots: float
    inside_window: bool
    positions_at_fire: int
    max_positions: int
    seconds_to_high_impact: float | None
    r_multiple: float | None = None
    pnl_usd: float | None = None
    closed_at: int | None = None


@dataclass(frozen=True)
class SessionRow:
    """One evening. Money comes from the account snapshots, never from summed fills."""

    session_id: str
    opened_at: int
    closed_at: int | None
    equity_open: float | None
    equity_close: float | None
    pre_rating: int | None = None
    post_rating: int | None = None
    stood_down_count: int = 0
    opportunity_quality: float | None = None
    note: str | None = None

    @property
    def session_return(self) -> float | None:
        """Return for the evening. `None` when the account figures are missing — never zero."""
        if not self.equity_open or self.equity_close is None:
            return None
        return (self.equity_close - self.equity_open) / self.equity_open

    @property
    def month(self) -> str:
        return datetime.fromtimestamp(self.opened_at / 1000, tz=UTC).strftime("%Y-%m")


# -- adherence ------------------------------------------------------------------------

# T-15: inside this window before a high-impact print, firing is off-process.
EVENT_GUARD_S = 900


def evaluate_fire(fire: Fire) -> dict[str, bool]:
    """Which rules this fire satisfied. One entry per rule in `ADHERENCE_RULES`."""
    return {
        "session_window": fire.inside_window,
        "max_lots": fire.lots <= fire.max_lots,
        "max_positions": fire.positions_at_fire < fire.max_positions,
        "named_setup": bool(fire.setup_tag),
        "event_guard": (
            fire.seconds_to_high_impact is None or fire.seconds_to_high_impact > EVENT_GUARD_S
        ),
    }


def rule_origin(rule_id: str) -> RuleOrigin:
    """Whether the gateway enforced this rule, or the deck is scoring it as a process habit."""
    return "gateway" if rule_id in GATEWAY_ADHERENCE_RULES else "process"


@dataclass(frozen=True)
class Adherence:
    """A session's adherence, and the per-rule breakdown that explains it."""

    score: float | None
    fires: int
    clean_fires: int
    by_rule: dict[str, float] = field(default_factory=dict)

    @property
    def has_data(self) -> bool:
        return self.fires > 0


def adherence_for(fires: list[Fire]) -> Adherence:
    """Fraction of fires that satisfied every rule.

    An evening with no fires has **no** adherence score rather than a zero: nothing was done
    off-process, so scoring it at zero would punish standing down — the exact thing this deck
    exists to avoid.
    """
    if not fires:
        return Adherence(score=None, fires=0, clean_fires=0, by_rule={})

    results = [evaluate_fire(fire) for fire in fires]
    clean = sum(1 for r in results if all(r.values()))
    by_rule = {
        rule: sum(1 for r in results if r[rule]) / len(results) for rule in ADHERENCE_RULES
    }
    return Adherence(score=clean / len(results), fires=len(results), clean_fires=clean,
                     by_rule=by_rule)


# -- outcome --------------------------------------------------------------------------


def returns_series(sessions: list[SessionRow]) -> list[float]:
    """Per-session returns, in order. Sessions with no account figures are absent, not zero."""
    ordered = sorted(sessions, key=lambda s: s.opened_at)
    return [r for r in (s.session_return for s in ordered) if r is not None]


def profit_factor(fires: list[Fire]) -> float | None:
    """Gross wins over gross losses. `None` when there is nothing to divide."""
    wins = sum(f.pnl_usd for f in fires if f.pnl_usd and f.pnl_usd > 0)
    losses = -sum(f.pnl_usd for f in fires if f.pnl_usd and f.pnl_usd < 0)
    if losses <= 0:
        return None if wins <= 0 else float("inf")
    return wins / losses


def average_r(fires: list[Fire]) -> float | None:
    values = [f.r_multiple for f in fires if f.r_multiple is not None]
    return sum(values) / len(values) if values else None


def win_rate(fires: list[Fire]) -> float | None:
    scored = [f for f in fires if f.pnl_usd is not None]
    if not scored:
        return None
    return sum(1 for f in scored if f.pnl_usd and f.pnl_usd > 0) / len(scored)


def max_drawdown(sessions: list[SessionRow]) -> float | None:
    """Deepest peak-to-trough fall of the compounded session-return curve."""
    series = returns_series(sessions)
    if not series:
        return None
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for value in series:
        equity *= 1 + value
        peak = max(peak, equity)
        worst = min(worst, equity / peak - 1)
    return worst


@dataclass(frozen=True)
class SharpeResult:
    """Sharpe with its sample size attached, always. A number alone would be misleading."""

    value: float | None
    sessions: int
    enough: bool
    note: str

    @property
    def display(self) -> str:
        if not self.enough or self.value is None:
            return "not enough sessions yet"
        return f"{self.value:.2f}"


def sharpe(
    sessions: list[SessionRow], min_sessions: int = DEFAULT_MIN_SESSIONS_FOR_SHARPE
) -> SharpeResult:
    """Annualised Sharpe, refused below `min_sessions`.

    Twenty evenings a month means the first two months of Sharpe are noise. Printing a confident
    2.4 after three weeks would be worse than printing nothing, so below the threshold the deck
    says how many sessions it has and how many it needs.
    """
    series = returns_series(sessions)
    count = len(series)
    if count < min_sessions:
        return SharpeResult(
            value=None, sessions=count, enough=False,
            note=f"{count} of {min_sessions} sessions — Sharpe stays hidden until there are enough",
        )
    deviation = statistics.stdev(series)
    if deviation == 0:
        return SharpeResult(value=None, sessions=count, enough=False,
                            note="no variation in the return series yet")
    value = (statistics.fmean(series) / deviation) * (SESSIONS_PER_YEAR**0.5)
    return SharpeResult(value=value, sessions=count, enough=True,
                        note=f"annualised from {count} sessions")


def by_setup(fires: list[Fire]) -> dict[str, dict[str, Any]]:
    """Per-setup outcome. Fires with no tag are grouped as `untagged`, not dropped."""
    groups: dict[str, list[Fire]] = {}
    for fire in fires:
        groups.setdefault(fire.setup_tag or "untagged", []).append(fire)
    return {
        tag: {
            "trades": len(group),
            "averageR": average_r(group),
            "winRate": win_rate(group),
            "profitFactor": profit_factor(group),
        }
        for tag, group in sorted(groups.items())
    }


# -- month over month -----------------------------------------------------------------


def group_by_month(sessions: list[SessionRow]) -> dict[str, list[SessionRow]]:
    grouped: dict[str, list[SessionRow]] = {}
    for session in sessions:
        grouped.setdefault(session.month, []).append(session)
    return grouped


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def process_month(sessions: list[SessionRow], fires: list[Fire]) -> dict[str, Any]:
    """One month of process figures. Every value may be `None` — absent is not zero."""
    ids = {s.session_id for s in sessions}
    month_fires = [f for f in fires if f.session_id in ids]
    adherence = adherence_for(month_fires)
    checkins = [float(s.pre_rating) for s in sessions if s.pre_rating is not None]
    checkins += [float(s.post_rating) for s in sessions if s.post_rating is not None]
    quality = [s.opportunity_quality for s in sessions if s.opportunity_quality is not None]
    declined = sum(s.stood_down_count for s in sessions)

    return {
        "sessions": len(sessions),
        "adherence": adherence.score,
        "adherenceByRule": adherence.by_rule,
        "fires": adherence.fires,
        "declined": declined,
        # Declined per session, so a busy month and a quiet one are comparable.
        "declinedRate": declined / len(sessions) if sessions else None,
        "checkinAverage": _mean(checkins),
        "opportunityQuality": _mean([q for q in quality if q is not None]),
    }


def outcome_month(sessions: list[SessionRow], fires: list[Fire]) -> dict[str, Any]:
    """One month of outcome figures. Behind a click, never on the process panel."""
    ids = {s.session_id for s in sessions}
    month_fires = [f for f in fires if f.session_id in ids]
    series = returns_series(sessions)
    compounded = 1.0
    for value in series:
        compounded *= 1 + value

    return {
        "sessions": len(sessions),
        "returnPct": (compounded - 1) if series else None,
        "averageR": average_r(month_fires),
        "winRate": win_rate(month_fires),
        "profitFactor": profit_factor(month_fires),
        "maxDrawdown": max_drawdown(sessions),
        "trades": len(month_fires),
    }


def delta(current: Any, previous: Any) -> float | None:
    """This month against last. `None` whenever either side is missing — never a fake zero."""
    if not isinstance(current, (int, float)) or not isinstance(previous, (int, float)):
        return None
    return float(current) - float(previous)


def month_over_month(
    sessions: list[SessionRow], fires: list[Fire], keys: list[str], builder: Any
) -> dict[str, Any]:
    """The primary 'am I improving?' answer: the last two months and the gap between them."""
    grouped = group_by_month(sessions)
    months = sorted(grouped)
    current = builder(grouped[months[-1]], fires) if months else builder([], fires)
    previous = builder(grouped[months[-2]], fires) if len(months) > 1 else None

    return {
        "month": months[-1] if months else None,
        "previousMonth": months[-2] if len(months) > 1 else None,
        "current": current,
        "previous": previous,
        "delta": {
            key: delta(current.get(key), (previous or {}).get(key)) for key in keys
        },
    }


def opportunity_verdict(quality: float | None, fires: int) -> str:
    """What a flat evening means. A dead tape and a missed evening are different things."""
    if fires > 0:
        return "traded"
    if quality is None:
        return "no opportunity reading for this evening"
    if quality < 0.33:
        return "dead tape — standing down was the read"
    if quality < 0.66:
        return "thin tape — few setups worth the spread"
    return "live tape, no fires — worth reviewing why"
