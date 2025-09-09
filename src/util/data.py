import datetime
import functools
import json
import os

EXAMPLE = 'example.jsonl'
FILENAME = os.getenv('TH_BL_FILE', EXAMPLE)
IS_DEMO = FILENAME == EXAMPLE


def read_data_from_file(filename):
    '''Read data from file with basic file modification caching'''
    data = []
    if not os.path.isfile(filename):
        return data
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
    for b in badges:
        b.pop('_line', None)
    return badges


read_data = functools.partial(read_data_from_file, filename=FILENAME)


def append_data_to_file(filename=None, contents=None):
    if filename is None or contents is None:
        return
    with open(filename, 'a') as file:    # perhaps we do a file per year
        file.write(f'{json.dumps(contents)}\n')


append_data = functools.partial(append_data_to_file, filename=FILENAME)
