"""Public-facing trainer name formatting.

On public pages we show a trainer's first name plus the initial of their last
name (e.g. ``"Alex Johnson"`` -> ``"Alex J."``). Names have a single first name
and one-or-more last names, so the initial is taken from the *first* last-name
word (``"Alex Von Johnson"`` -> ``"Alex V."``).

When two trainers would collapse to the same abbreviation, a stable numeric
index disambiguates them (``"Alex J. 1"`` / ``"Alex J. 2"``). The index set is
built from every trainer in the data so a given person renders the same way on
every page.

Admin pages intentionally keep full names -- only call these from public views.
"""
from __future__ import annotations

import functools
from collections import defaultdict

import util.seasons


def abbreviate(full_name) -> str:
    """First name + last-name initial. Single-word names pass through."""
    parts = (full_name or '').split()
    if len(parts) < 2:
        return full_name or ''
    return f'{parts[0]} {parts[1][0].upper()}.'


@functools.lru_cache(maxsize=64)
def _display_map(names: frozenset) -> dict:
    """Map each full name to a unique abbreviation, indexing collisions."""
    groups: defaultdict = defaultdict(list)
    for name in names:
        groups[abbreviate(name)].append(name)
    result = {}
    for abbr, members in groups.items():
        if len(members) == 1:
            result[members[0]] = abbr
        else:
            # Deterministic order so the same person keeps the same index.
            for i, name in enumerate(sorted(members), start=1):
                result[name] = f'{abbr} {i}'
    return result


def _all_trainer_names() -> frozenset:
    names = {b.get('trainer') for b in util.seasons.read_badges() if b.get('trainer')}
    return frozenset(names)


def public_name(full_name) -> str:
    """Return the public display name for a trainer (abbreviated, deduped)."""
    if not full_name:
        return full_name
    return _display_map(_all_trainer_names()).get(full_name, abbreviate(full_name))
