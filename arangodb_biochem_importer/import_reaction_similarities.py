import time
import sys
import os
import csv

from init_db import init_db

similarity_threshold = 0.0


def import_similarities(file_path):
    """
    Iterate over every row in a TSV file and import each as a compound document.
    We don't yet create edges for compounds.
    """
    reaction_similar_to = db.collections['reaction_similar_to']
    with open(file_path, newline='') as csv_fd:
        reader = csv.reader(csv_fd, delimiter=' ', quotechar='"')
        to_insert = []
        for row in reader:
            row = ['reactions/' + row[0], 'reactions/' + row[1], float(row[2])]
            if row[2] < similarity_threshold:
                continue
            doc = {'_from': row[0], '_to': row[1], 'similarity': row[2]}
            to_insert.append(doc)
    print('importing %s total reaction similarities' % len(to_insert))
    result = reaction_similar_to.bulkSave(to_insert, onDuplicate="replace")
    print('successfully imported.')
    return result


if __name__ == '__main__':
    """
    Simple command-line API:
    python arangodb_biochem_importer/import_compounds.py <path-to-directory-of-compound-files>

    Where all compound files are TSVs with the file name '*compounds.tsv'
    """
    start = int(time.time() * 1000)
    if len(sys.argv) <= 1:
        sys.stderr.write('Provide the file path of a TSV containing similarity data.')
        exit(1)
    db = init_db()
    file_path = os.path.abspath(sys.argv[1])
    result = import_similarities(file_path)
    print('total running time in ms: %d' % (int(time.time() * 1000) - start))
