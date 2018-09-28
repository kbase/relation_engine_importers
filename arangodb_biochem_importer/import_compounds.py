"""
Iterate over a directory and find all files called "*compounds.tsv"
For each file:
- Get the tsv headers
- Change the 'id' column into '_key' and snake case the others
- Read the TSV file into an array of strings or something
- Snake case all the columns
- Import each row as a plain document in the 'compound' collection
"""
import time
import sys
import os
import re
import csv

from init_db import init_db
from setup_collections import setup_collections


# Transformations on the header names
# Eg. given a header "id", save it as a field named "_key" in the db
header_transforms = {
    'id': '_key',
    'kegg id': 'kegg_id',
    'ms id': 'ms_id'
}


if __name__ == '__main__':
    start = int(time.time() * 1000)
    if len(sys.argv) <= 1:
        sys.stderr.write('Provide the directory path containing *compounds.tsv files.')
        exit(1)
    db = init_db()
    vertices = ['compound']
    setup_collections(db, vertices, [])
    compound = db.collections['compound']
    print(dir(compound))
    compounds_dir = os.path.abspath(sys.argv[1])
    file_pattern = r'.*compounds\.tsv'
    for filename in os.listdir(compounds_dir):
        if not re.search(file_pattern, filename):
            continue
        fullpath = os.path.join(compounds_dir, filename)
        print('importing from tsv file %s' % fullpath)
        with open(fullpath, newline='') as csv_fd:
            reader = csv.reader(csv_fd, delimiter='\t', quotechar='"')
            headers = next(reader)
            for (idx, h) in enumerate(headers):
                headers[idx] = header_transforms.get(h, h)
            count = 0
            to_insert = []
            for row in reader:
                row_data = {}  # type: dict
                to_insert.append(row_data)
                for (idx, col) in enumerate(row):
                    row_data[headers[idx]] = col
        result = compound.bulkSave(to_insert, onDuplicate="update")
        print('Saved compounds', result)
    end = int(time.time() * 1000)
    print('total running time in ms: %d' % (end - start))
