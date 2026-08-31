"""The mistake taxonomy, and what the gateway can honestly prove about one.

The split that makes this usable rather than accusatory:

- **auto** mistakes are things the rows already prove. An oversize fire, a missing initial stop, a
  stop moved further away, a fire inside the event window — each of those is a fact with a row
  behind it, and naming it is not a judgement.
- **player** mistakes are the rest. Revenge re-entry and early discretionary exit describe intent,
  and no amount of evidence turns a tape into a state of mind. Evidence can *suggest* one; the
  player asserts it.

There is no streak, no badge, and no penalty. A mistake is counted, trended, and optionally chosen
as the one thing being worked on. Nothing about it touches the Process Score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# T-15: inside this window before a high-impact print, firing is off-process. Phase 6's number,
# imported rather than restated so the journal and the deck cannot disagree about it.
from deck.metrics import EVENT_GUARD_S

# Where a mistake can come from. `auto` means the gateway proved it from a row.
Source = str


@dataclass(frozen=True)
class MistakeDef:
    """One entry in the taxonomy. Custom mistakes are the same shape with `builtin` false."""

    code: str
    label: str
    builtin: bool = True
    # Whether the gateway can derive this from rows, or whether it needs the player to say so.
    derivable: bool = False


BUILTINS: tuple[MistakeDef, ...] = (
    MistakeDef("oversize", "Oversized for the cap", derivable=True),
    MistakeDef("no_initial_sl", "No stop at entry", derivable=True),
    MistakeDef("worsened_sl", "Stop moved further away", derivable=True),
    MistakeDef("event_window", "Fired inside the event window", derivable=True),
    MistakeDef("outside_session", "Fired outside the session window", derivable=True),
    MistakeDef("no_playbook", "Wrong or no playbook", derivable=True),
    MistakeDef("skipped_review", "Skipped the review", derivable=True),
    # These three describe intent. The tape cannot prove any of them.
    MistakeDef("early_exit", "Closed early on discretion"),
    MistakeDef("chased_entry", "Chased the entry"),
    MistakeDef("revenge_entry", "Revenge re-entry"),
)

BUILTIN_CODES = tuple(m.code for m in BUILTINS)
DERIVABLE = {m.code for m in BUILTINS if m.derivable}


def seed_rows(ts_ms: int) -> list[tuple[str, str, int, int, int]]:
    """Rows for `mistake_definition`, applied once at boot."""
    return [(m.code, m.label, 1, 1, ts_ms) for m in BUILTINS]


@dataclass(frozen=True)
class FireEvidence:
    """The facts a derivable mistake is read off. `None` is *not measured*, never a breach."""

    cid: str
    session_id: str | None = None
    lots: float | None = None
    max_lots: float | None = None
    planned_sl: float | None = None
    side: str = "buy"
    amendments: tuple[dict[str, Any], ...] = ()
    seconds_to_high_impact: float | None = None
    inside_window: bool | None = None
    playbook_id: str | None = None
    checklist_answered: bool | None = None
    replay_opened: bool | None = None


def derive(evidence: FireEvidence) -> list[str]:
    """Every mistake the rows actually prove for this fire.

    Nothing is returned on missing evidence. A trade whose cap was never recorded is a trade with
    no cap evidence — treating that as an oversize would invent a breach out of a null column.
    """
    from .metrics import worsened_stops

    found: list[str] = []

    if evidence.lots is not None and evidence.max_lots is not None and evidence.lots > evidence.max_lots:
        found.append("oversize")
    if evidence.planned_sl is None:
        found.append("no_initial_sl")
    if worsened_stops(evidence.amendments, side=evidence.side, original_sl=evidence.planned_sl):
        found.append("worsened_sl")
    if (evidence.seconds_to_high_impact is not None
            and evidence.seconds_to_high_impact <= EVENT_GUARD_S):
        found.append("event_window")
    if evidence.inside_window is False:
        found.append("outside_session")
    if not evidence.playbook_id or evidence.playbook_id == "__unplanned__":
        found.append("no_playbook")
    # Skipped review is only claimable once both halves are known to be absent.
    if evidence.checklist_answered is False and evidence.replay_opened is False:
        found.append("skipped_review")

    return found


def trend(occurrences: list[dict[str, Any]], *, focus: str | None = None) -> dict[str, Any]:
    """Frequency and affected trades per mistake, plus the one thing being worked on.

    Counts, never a penalty. The improvement focus is a single optional code — one thing at a time
    is the whole idea, and a leaderboard of your own failures is not a training aid.
    """
    by_code: dict[str, dict[str, Any]] = {}
    for row in occurrences:
        entry = by_code.setdefault(row["code"], {"code": row["code"], "count": 0, "trades": set(),
                                                 "auto": 0, "player": 0})
        entry["count"] += 1
        entry["trades"].add(row["cid"])
        entry["auto" if row.get("source") == "auto" else "player"] += 1

    ranked = sorted(by_code.values(), key=lambda e: (-e["count"], e["code"]))
    return {
        "mistakes": [
            {"code": e["code"], "count": e["count"], "trades": len(e["trades"]),
             "auto": e["auto"], "player": e["player"]}
            for e in ranked
        ],
        "focus": focus,
        # Said out loud so nobody adds one later by accident.
        "note": "counts only — no streak, badge, or penalty",
    }
