import datetime
import functools
import json
import os

FILENAME = os.getenv('TH_BL_FILE', 'example.jsonl')


def read_data_from_file(filename):
    '''Read data from file with basic file modification caching'''
    data = []
    if not os.path.isfile(filename):
        return data
    with open(filename, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue  # Skip invalid lines
    for b in data:
        try:
            b['date'] = datetime.date.fromisoformat(b.get('date'))
        except Exception:
            b['date'] = None
    badges = sorted(data, key=lambda x: x['date'], reverse=True)
    return badges


read_data = functools.partial(read_data_from_file, filename=FILENAME)


def append_data_to_file(filename, contents):
    with open(filename, 'a') as file:    # perhaps we do a file per year
        file.write(f'{json.dumps(contents)}\n')


append_data = functools.partial(append_data_to_file, filename=FILENAME)
