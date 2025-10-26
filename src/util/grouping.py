from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

Badge = Dict[str, Any]
GroupKey = Any


def group_badges(
    badges: Iterable[Badge],
    key_getter: Callable[[Badge], GroupKey],
) -> Dict[GroupKey, List[Badge]]:
    """Group badges by the provided key function, skipping empty keys."""
    grouped: Dict[GroupKey, List[Badge]] = defaultdict(list)
    for badge in badges:
        key = key_getter(badge)
        if not key:
            continue
        grouped[key].append(badge)
    return grouped


def sort_group_items(
    groups: Dict[GroupKey, Sequence[Badge]],
    *,
    sort_key: Optional[Callable[[Tuple[GroupKey, Sequence[Badge]]], Any]] = None,
) -> List[Tuple[GroupKey, List[Badge]]]:
    """Return grouped items sorted by the provided key or default ordering."""
    items = [(key, list(value)) for key, value in groups.items()]
    if sort_key is None:
        items.sort(key=lambda item: (-len(item[1]), item[0]))
    else:
        items.sort(key=sort_key)
    return items


def dropdown_options(
    group_items: Iterable[Tuple[GroupKey, Sequence[Badge]]],
    label_fn: Callable[[GroupKey, Sequence[Badge]], str],
    *,
    value_fn: Optional[Callable[[GroupKey, Sequence[Badge]], Any]] = None,
) -> List[Dict[str, Any]]:
    """Create dropdown options from grouped badge items."""
    options = []
    for key, badges in group_items:
        option_value = value_fn(key, badges) if value_fn else key
        options.append({
            "label": label_fn(key, badges),
            "value": option_value,
        })
    return options
