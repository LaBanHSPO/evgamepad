"""The calendar degrades in three documented steps and never fails the evening."""

from __future__ import annotations

import json
from pathlib import Path

from signals.calendar import MAX_EVENTS, CalendarCache, normalise

ROWS = [
    {"title": "Non-Farm Payrolls", "country": "USD", "impact": "High",
     "date": "2023-11-14T22:20:00Z"},
    {"title": "Retail Sales", "country": "GBP", "impact": "Medium",
     "date": "2023-11-15T09:30:00Z"},
    {"title": "Bank Holiday", "country": "JPY", "impact": "Holiday",
     "date": "2023-11-16T00:00:00Z"},
]
NOW_MS = 1_699_900_000_000


def cache_at(tmp_path: Path, **kw) -> CalendarCache:
    return CalendarCache(cache_path=tmp_path / "ff.json", timezone="Asia/Ho_Chi_Minh",
                         source="off", **kw)


def test_rows_normalise_into_the_session_zone() -> None:
    events = normalise(ROWS, "Asia/Ho_Chi_Minh")
    assert [e.title for e in events] == ["Non-Farm Payrolls", "Retail Sales", "Bank Holiday"]
    assert events[0].currency == "USD"
    assert ":" in events[0].local, "events carry a local display string"


def test_a_malformed_row_is_dropped_rather_than_fatal() -> None:
    events = normalise([*ROWS, {"title": "broken"}, {"date": "not-a-date", "title": "x",
                                                     "country": "USD"}], "UTC")
    assert len(events) == 3


def test_the_feed_is_capped_because_it_is_untrusted_input() -> None:
    flood = [dict(ROWS[0]) for _ in range(MAX_EVENTS + 250)]
    assert len(normalise(flood, "UTC")) == MAX_EVENTS


def test_source_off_reads_the_local_file(tmp_path: Path) -> None:
    fallback = tmp_path / "calendar.yaml"
    fallback.write_text(json.dumps({"events": ROWS}), encoding="utf-8")
    calendar = cache_at(tmp_path, fallback_path=fallback)

    events = calendar.events()
    assert len(events) == 3
    assert calendar.status == "file"


def test_no_feed_and_no_file_is_a_state_not_a_crash(tmp_path: Path) -> None:
    calendar = cache_at(tmp_path)
    assert calendar.events() == []
    assert calendar.status == "offline"


def test_upcoming_filters_by_impact_and_by_the_basket(tmp_path: Path) -> None:
    fallback = tmp_path / "calendar.yaml"
    fallback.write_text(json.dumps({"events": ROWS}), encoding="utf-8")
    calendar = cache_at(tmp_path, fallback_path=fallback)

    high = calendar.upcoming(NOW_MS, min_impact="High")
    assert [e.title for e in high] == ["Non-Farm Payrolls"]

    gbp = calendar.upcoming(NOW_MS, currencies=["GBP"], min_impact="Medium")
    assert [e.title for e in gbp] == ["Retail Sales"]

    assert calendar.upcoming(NOW_MS, currencies=["CHF"], min_impact="Low") == []


def test_past_events_are_not_upcoming(tmp_path: Path) -> None:
    fallback = tmp_path / "calendar.yaml"
    fallback.write_text(json.dumps({"events": ROWS}), encoding="utf-8")
    calendar = cache_at(tmp_path, fallback_path=fallback)
    assert calendar.upcoming(1_800_000_000_000, min_impact="Low") == []


def test_the_guard_only_fires_inside_the_window(tmp_path: Path) -> None:
    fallback = tmp_path / "calendar.yaml"
    fallback.write_text(json.dumps({"events": ROWS}), encoding="utf-8")
    calendar = cache_at(tmp_path, fallback_path=fallback)

    nfp_ms = 1_700_000_400_000  # 2023-11-14T22:20:00Z
    assert calendar.guard(nfp_ms - 600_000, ["USD"]) is not None, "10 minutes out is a wait"
    assert calendar.guard(nfp_ms - 3_600_000, ["USD"]) is None, "an hour out is not"


def test_a_cached_file_is_preferred_over_nothing(tmp_path: Path) -> None:
    """A week-old calendar still knows when NFP is."""
    cache = tmp_path / "ff.json"
    cache.write_text(json.dumps(ROWS), encoding="utf-8")
    calendar = CalendarCache(cache_path=cache, timezone="UTC", source="ff_weekly",
                             url="http://127.0.0.1:9/nope")

    events = calendar.events()
    assert len(events) == 3
    assert calendar.status == "cached"
