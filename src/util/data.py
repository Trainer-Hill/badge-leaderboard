import datetime
import functools
import json
import os

EXAMPLE = 'example.jsonl'

# Directory holding the JSONL data files. Empty by default, so paths stay
# relative to the working dir exactly as before (local dev is unchanged). In
# Docker we set TH_BL_DATA_DIR to a bind-mounted directory (e.g. /app/data) so
# individual files don't need to pre-exist -- the app creates them on write.
DATA_DIR = os.getenv('TH_BL_DATA_DIR', '')


def data_path(name):
    """Resolve a data filename against DATA_DIR (a no-op when DATA_DIR is empty)."""
    return os.path.join(DATA_DIR, name)


FILENAME = data_path(os.getenv('TH_BL_FILE', EXAMPLE))
IS_DEMO = os.path.basename(FILENAME) == EXAMPLE
_READ_CACHE = {}


def _get_file_version(filename):
    try:
        stats = os.stat(filename)
    except FileNotFoundError:
        return None
    return (stats.st_mtime_ns, stats.st_size)


def read_data_from_file(filename):
    '''Read data from file with basic file modification caching'''
    file_version = _get_file_version(filename)
    if file_version is None:
        _READ_CACHE.pop(filename, None)
        return []

    cached = _READ_CACHE.get(filename)
    if cached and cached['version'] == file_version:
        return cached['data']

    data = []
    with open(filename, 'r') as f:
        for i, line in enumerate(f):
            try:
                badge = json.loads(line.strip())
                badge['_line'] = i
                data.append(badge)
            except json.JSONDecodeError:
                continue  # Skip invalid lines
    for b in data:
        try:
            b['date'] = datetime.date.fromisoformat(b.get('date'))
        except Exception:
            b['date'] = None
    badges = sorted(
        data,
        key=lambda x: (
            x['date'] or datetime.date.min,
            x.get('_line', 0),
        ),
        reverse=True,
    )
    _READ_CACHE[filename] = {'version': file_version, 'data': badges}
    return badges


def update_data_in_file(filename=None, line_index=None, contents=None):
    if filename is None or line_index is None or contents is None:
        return
    safe = {k: v for k, v in contents.items() if k != '_line'}
    with open(filename, 'r') as f:
        lines = f.readlines()
    if line_index >= len(lines):
        return
    lines[line_index] = f'{json.dumps(safe)}\n'
    with open(filename, 'w') as f:
        f.writelines(lines)
    _READ_CACHE.pop(filename, None)


update_data = functools.partial(update_data_in_file, filename=FILENAME)


read_data = functools.partial(read_data_from_file, filename=FILENAME)


def append_data_to_file(filename=None, contents=None):
    if filename is None or contents is None:
        return
    parent = os.path.dirname(filename)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(filename, 'a') as file:    # 'a' creates the file if it doesn't exist
        file.write(f'{json.dumps(contents)}\n')
    _READ_CACHE.pop(filename, None)


append_data = functools.partial(append_data_to_file, filename=FILENAME)
