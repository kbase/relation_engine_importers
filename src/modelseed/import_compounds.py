"""
Iterate over a directory and find all files called "*compounds.tsv"
For each file:
- Get the tsv headers
- Change the 'id' column into '_key' and snake case the others
- Read the TSV file into an array of strings or something
- Snake case all the columns
- Import each row as a plain document in the 'compounds' collection
"""
import time
import sys
import os
import re
import csv

from utils.init_db import init_db
# TODO this module does not exist any longer
from setup_collections import setup_collections


# Transformations on the header names
# Eg. given a header "id", save it as a field named "_key" in the db
header_transforms = {
    'id': '_key',
    'kegg id': 'kegg_id',
    'ms id': 'ms_id'
}


def setup():
    """Initialize the db connection and collections and return the connection."""
    db = init_db()
    vertices = ['compounds']
    setup_collections(db, vertices, [])
    return db


def import_compounds(file_path):
    """
    Iterate over every row in a TSV file and import each as a compound document.
    We don't yet create edges for compounds.
    """
    compounds = db.collections['compounds']
    with open(file_path, newline='') as csv_fd:
        reader = csv.reader(csv_fd, delimiter='\t', quotechar='"')
        headers = next(reader)
        for (idx, h) in enumerate(headers):
            headers[idx] = header_transforms.get(h, h)
        to_insert = []
        for row in reader:
            row_data = {}  # type: dict
            to_insert.append(row_data)
            for (idx, col) in enumerate(row):
                row_data[headers[idx]] = col
            # Remove any *_c0 or *_e0 suffixes
            row_data['_key'] = row_data['_key'].replace('_c0', '').replace('_e0', '')
    result = compounds.bulkSave(to_insert, onDuplicate="update")
    return result


def get_compound_files(dir_path):
    """Get all the compound filepaths for a directory ('*compounds.tsv')"""
    file_pattern = r'.*compounds\.tsv'
    for file_name in os.listdir(dir_path):
        if re.search(file_pattern, file_name):
            # Yield the full path
            yield os.path.join(dir_path, file_name)


if __name__ == '__main__':
    """
    Simple command-line API:
    python arangodb_biochem_importer/import_compounds.py <path-to-directory-of-compound-files>

    Where all compound files are TSVs with the file name '*compounds.tsv'
    """
    start = int(time.time() * 1000)
    if len(sys.argv) <= 1:
        sys.stderr.write('Provide the directory path containing *compounds.tsv files.')
        exit(1)
    db = setup()
    compounds_dir = os.path.abspath(sys.argv[1])
    for file_path in get_compound_files(compounds_dir):
        print('importing from tsv file %s' % file_path)
        result = import_compounds(file_path)
        print('Saved compounds', result)
    print('total running time in ms: %d' % (int(time.time() * 1000) - start))
