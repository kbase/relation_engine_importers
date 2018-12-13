import time
import sys
import os
import csv

from utils.init_db import init_db

_similar_edge_name = 'rxn_similar_to_reaction'
_reaction_vert_name = 'rxn_reaction'


def import_similarities(file_path):
    """
    Iterate over every row in a TSV file and import each as a compound document.
    We don't yet create edges for compounds.
    """
    reaction_similar_to = db.collections[_similar_edge_name]
    with open(file_path, newline='') as csv_fd:
        reader = csv.reader(csv_fd, delimiter=' ', quotechar='"')
        to_insert = []
        for row in reader:
            doc = {
                '_from': _reaction_vert_name + '/' + row[0],
                '_to': _reaction_vert_name + '/' + row[1],
                'sf_similarity': float(row[2]),
                'df_similarity': float(row[3])
            }
            to_insert.append(doc)
    print('importing %s total reaction similarities' % len(to_insert))
    result = reaction_similar_to.bulkSave(to_insert, onDuplicate="replace")
    print('successfully imported.')
    return result


if __name__ == '__main__':
    """
    Simple command-line API:
    python arangodb_biochem_importer/import_reaction_similarities.py <path-to-file>
    """
    start = int(time.time() * 1000)
    if len(sys.argv) < 2:
        sys.stderr.write('Provide the file path of a csv containing similarity data.\n')
        exit(1)
    db = init_db()
    file_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(file_path):
        sys.stderr.write('%s does not exist\n' % file_path)
        exit(1)
    result = import_similarities(file_path)
    print('total running time in ms: %d' % (int(time.time() * 1000) - start))
