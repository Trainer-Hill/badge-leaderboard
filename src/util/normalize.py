"""Normalize raw season records into the common badge shape all pages consume.

Seasons can store data in different shapes depending on their ``mode`` (see
``util.seasons``):

- ``badges`` mode: each line is already a badge record. We validate and pass it
  through, surfacing warnings for missing expected fields.
- ``events`` mode (future): each line is an *event* with an embedded list of
  ``standings``. Badges are derived from the standings where ``earned_badge`` is
  true. ``earned_badge`` is set explicitly by the admin -- it is never inferred
  from placement -- because badge-earning rules change year to year.

Pages should never read raw records directly; they go through this layer so both
shapes degrade gracefully to the same internal badge dict.
"""
from __future__ import annotations

from typing import List, Tuple

# Fields we expect on a badge. Missing ones are logged, not fatal.
_EXPECTED_BADGE_FIELDS = ('trainer', 'deck', 'date', 'tier')

# Event-level fields copied onto each derived badge.
_EVENT_FIELDS = ('store', 'date', 'tier', 'format', 'background')


def _record_label(record: dict) -> str:
    """A short human identifier for warning messages."""
    ident = record.get('id') or record.get('trainer') or record.get('store')
    line = record.get('_line')
    if line is not None:
        return f'{ident} (line {line})'
    return str(ident)


def _normalize_badge_record(record: dict) -> Tuple[dict, List[str]]:
    """Validate a badge-mode record and pass it through unchanged."""
    warnings = [
        f'Badge {_record_label(record)} missing field "{field}"'
        for field in _EXPECTED_BADGE_FIELDS
        if not record.get(field)
    ]
    return record, warnings


def _normalize_event_record(record: dict) -> Tuple[List[dict], List[str]]:
    """Derive badge records from an event's standings.

    A standing earns a badge only when ``earned_badge`` is explicitly true.
    """
    warnings: List[str] = []
    standings = record.get('standings') or []
    if not standings:
        warnings.append(f'Event {_record_label(record)} recorded with no standings')
        return [], warnings

    event_meta = {k: record.get(k) for k in _EVENT_FIELDS if record.get(k) is not None}

    badges: List[dict] = []
    for standing in standings:
        if not standing.get('earned_badge'):
            continue
        badge = dict(event_meta)
        # Standing-level fields win over event-level ones (e.g. a per-standing date).
        badge.update({
            k: v for k, v in standing.items()
            if k not in ('earned_badge', 'placement', 'record')
        })
        # Carry provenance so pages/admin can trace a badge back to its event.
        badge['event_id'] = record.get('id')
        badge['_line'] = record.get('_line')
        badges.append(badge)

    if not badges:
        warnings.append(
            f'Event {_record_label(record)} has standings but none earned a badge'
        )
    return badges, warnings


def normalize_records(records, mode: str = 'badges') -> Tuple[List[dict], List[str]]:
    """Convert raw season records into badge dicts.

    Returns ``(badges, warnings)``. Unknown modes fall back to ``badges`` so a
    misconfigured season degrades rather than errors.
    """
    badges: List[dict] = []
    warnings: List[str] = []

    for record in records:
        if not isinstance(record, dict):
            continue
        if mode == 'events':
            derived, warns = _normalize_event_record(record)
            badges.extend(derived)
        else:
            badge, warns = _normalize_badge_record(record)
            badges.append(badge)
        warnings.extend(warns)

    return badges, warnings
