"""Report composition: existing journal queries, arranged for print.

There is no new arithmetic here. Every figure comes from the phase that owns it — adherence from
the deck, the axes from the score, the trend from the journal — because a report that recomputes a
number is a second implementation waiting to disagree with the first.

**Process pages come first and the money is an appendix.** That ordering is the report, not a
default someone can flip: the outcome section is only assembled when it is explicitly asked for, so
a report saved without it never contained a dollar figure to begin with.

PDF is the browser's own Save as PDF over a print stylesheet. Putting Chromium on the VPS to render
a monthly summary would be several hundred megabytes and a second attack surface for a job the
machine in front of the player already does.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Period = Literal["week", "month", "custom", "session"]

DAY_MS = 86_400_000
WINDOWS: dict[str, int] = {"week": 7 * DAY_MS, "month": 31 * DAY_MS}


def resolve_window(period: Period, *, from_ms: int | None, to_ms: int | None,
                   now_ms: int) -> tuple[int | None, int | None]:
    """The period as a pair of timestamps. `custom` and `session` pass through untouched."""
    if period in WINDOWS:
        return now_ms - WINDOWS[period], now_ms
    return from_ms, to_ms


@dataclass
class ReportBuilder:
    """Assembles one report from the surfaces that already exist."""

    db_path: Path
    deck: Any
    score: Any
    journal: Any

    def build(
        self, *, period: Period = "month", from_ms: int | None = None, to_ms: int | None = None,
        session_id: str | None = None, include_outcome: bool = False,
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        """The whole report. `outcome` is absent unless it was asked for by name."""
        stamp = now_ms if now_ms is not None else int(time.time() * 1000)
        start, end = resolve_window(period, from_ms=from_ms, to_ms=to_ms, now_ms=stamp)

        # A single-session report is a different shape: one evening in full, not a period summary.
        if period == "session" and session_id:
            return self._session_report(session_id, include_outcome=include_outcome, now_ms=stamp)

        overview = self.journal.overview(from_ms=start, to_ms=end)
        days = self.journal.days(from_ms=start, to_ms=end)["days"]
        scored = [day for day in days if day["score"] is not None]

        report: dict[str, Any] = {
            "kind": "period",
            "period": period,
            "from": start,
            "to": end,
            "generatedAt": stamp,
            # The cover is process only. There is no money on it in any configuration.
            "cover": {
                "sessions": overview["sessions"],
                "trades": sum(day["trades"] for day in days),
                "declined": sum(day["declined"] for day in days),
                "consistency": overview["consistency"],
                "processScoreMean": overview["processScoreMean"],
                "scoredSessions": len(scored),
            },
            "heatmap": days,
            "process": self.deck.process(),
            "playbooks": self.deck.playbooks(outcome=False)["playbooks"],
            "mistakes": overview["mistakes"],
            "groups": overview["groups"],
            "disclaimer": "cTrader demo · entertainment, not advice",
        }

        if include_outcome:
            # Assembled only on request, so a report saved without it never held the figures.
            report["outcome"] = {
                "summary": self.deck.outcome(),
                "playbooks": self.deck.playbooks(outcome=True)["playbooks"],
            }
        return report

    def _session_report(self, session_id: str, *, include_outcome: bool,
                        now_ms: int) -> dict[str, Any]:
        day = self.journal.day(session_id)
        report: dict[str, Any] = {
            "kind": "session",
            "period": "session",
            "sessionId": session_id,
            "generatedAt": now_ms,
            "cover": {
                "sessions": 1,
                "trades": len(day.get("trades", [])),
                "declined": (day.get("checkin") or {}).get("declined", 0),
                "score": day.get("score"),
            },
            "readiness": day.get("readiness", []),
            "analysis": day.get("analysis"),
            "score": self.score.session_payload(session_id),
            "tilt": self.deck.tilt_retro(session_id),
            "trades": day.get("trades", []),
            "mistakes": day.get("mistakes", []),
            "disclaimer": "cTrader demo · entertainment, not advice",
        }
        if include_outcome:
            report["outcome"] = {"summary": self.deck.outcome()}
        return report


# The keys a report may carry when the outcome appendix is off. Exported so the test can assert the
# absence rather than trusting the builder to have remembered.
PROCESS_ONLY_KEYS = ("kind", "period", "from", "to", "generatedAt", "cover", "heatmap", "process",
                     "playbooks", "mistakes", "groups", "disclaimer")
