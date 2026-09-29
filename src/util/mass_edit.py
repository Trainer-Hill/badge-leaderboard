"""Bulk-edit raw records across every data file.

A trainer or a deck can show up under a wrong name for a long time before
someone notices (e.g. a lower-division trainer entered as "John D." who has
since started earning badges under "John Doe", or a deck stood in with a
sample Pokemon before its real sprite existed). Fixing that means rewriting
every occurrence, and occurrences live in different shapes depending on the
season's mode (see :mod:`util.seasons`): a top-level field on a badges-mode
line, or nested in an events-mode record's ``standings`` list.

This module reads and rewrites those raw records directly -- it does not go
through :mod:`util.normalize`, since a rename has to reach standings, not just
the derived badge view pages consume.
"""
from __future__ import annotations

import datetime
from typing import Dict, Iterable, List

import util.data
import util.seasons


def _serializable(record: dict) -> dict:
    """Copy of ``record`` with its ``date`` JSON-safe again.

    util.data.read_data_from_file parses ``date`` into a ``datetime.date`` on
    the way in; writing it back out has to undo that or json.dumps blows up.
    """
    copy = dict(record)
    date = copy.get('date')
    if isinstance(date, datetime.date):
        copy['date'] = date.isoformat()
    return copy


def _write_back(filename: str, record: dict) -> None:
    util.data.update_data_in_file(
        filename=filename,
        line_index=record['_line'],
        contents=_serializable(record),
    )


def trainer_counts() -> Dict[str, int]:
    """Trainer name -> number of participant records (badge or not) mentioning them."""
    counts: Dict[str, int] = {}
    for badge in util.seasons.read_participants():
        trainer = badge.get('trainer')
        if trainer:
            counts[trainer] = counts.get(trainer, 0) + 1
    return counts


def deck_counts() -> Dict[str, dict]:
    """Deck id -> {'deck': deck_dict, 'count': n} for every distinct deck seen."""
    decks: Dict[str, dict] = {}
    for badge in util.seasons.read_participants():
        deck = badge.get('deck')
        if isinstance(deck, dict) and deck.get('id'):
            entry = decks.setdefault(deck['id'], {'deck': deck, 'count': 0})
            entry['count'] += 1
    return decks


def rename_trainer(old_name: str, new_name: str) -> int:
    """Rewrite every occurrence of ``old_name`` as ``new_name`` across every
    data file. Returns the number of records (badge lines or events) touched.
    """
    old_name = (old_name or '').strip()
    new_name = (new_name or '').strip()
    if not old_name or not new_name or old_name == new_name:
        return 0

    touched = 0
    for filename, mode in util.seasons.data_files().items():
        for record in util.data.read_data_from_file(filename):
            changed = False
            if mode == 'events':
                for standing in record.get('standings') or []:
                    if standing.get('trainer') == old_name:
                        standing['trainer'] = new_name
                        changed = True
            elif record.get('trainer') == old_name:
                record['trainer'] = new_name
                changed = True
            if changed:
                _write_back(filename, record)
                touched += 1
    return touched


def update_pronouns(trainer_name: str, pronoun: str) -> int:
    """Set the ``pronouns`` field on every record for ``trainer_name`` across
    every data file. Returns the number of records touched.
    """
    trainer_name = (trainer_name or '').strip()
    pronoun = (pronoun or '').strip()
    if not trainer_name or not pronoun:
        return 0

    touched = 0
    for filename, mode in util.seasons.data_files().items():
        for record in util.data.read_data_from_file(filename):
            changed = False
            if mode == 'events':
                for standing in record.get('standings') or []:
                    if standing.get('trainer') == trainer_name and standing.get('pronouns') != pronoun:
                        standing['pronouns'] = pronoun
                        changed = True
            elif record.get('trainer') == trainer_name and record.get('pronouns') != pronoun:
                record['pronouns'] = pronoun
                changed = True
            if changed:
                _write_back(filename, record)
                touched += 1
    return touched


def replace_deck(old_ids: Iterable[str], new_deck: dict) -> int:
    """Repoint every badge/standing whose deck id is in ``old_ids`` at
    ``new_deck`` (a ``{id, name, icons}`` dict). Returns records touched.
    """
    old_ids = {i for i in old_ids if i}
    new_id = (new_deck or {}).get('id')
    if not old_ids or not new_id:
        return 0
    old_ids.discard(new_id)  # merging a deck onto itself is a no-op for that id
    if not old_ids:
        return 0

    touched = 0
    for filename, mode in util.seasons.data_files().items():
        for record in util.data.read_data_from_file(filename):
            changed = False
            if mode == 'events':
                for standing in record.get('standings') or []:
                    deck = standing.get('deck')
                    if isinstance(deck, dict) and deck.get('id') in old_ids:
                        standing['deck'] = dict(new_deck)
                        changed = True
            else:
                deck = record.get('deck')
                if isinstance(deck, dict) and deck.get('id') in old_ids:
                    record['deck'] = dict(new_deck)
                    changed = True
            if changed:
                _write_back(filename, record)
                touched += 1
    return touched
