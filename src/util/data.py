import json
import os

def read_data(filename):
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
    data.reverse()
    return data


def append_datafile(filename, contents):
    with open(filename, 'a') as file:    # perhaps we do a file per year
        file.write(f'{json.dumps(contents)}\n')
