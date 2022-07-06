import time
import sys
import os
import csv

import json

_similar_edge_name = 'rxn_similar_to_reaction'
_reaction_vert_name = 'rxn_reaction'


def convert_similarities(in_file_path, out_json_file_path):
    """
    Iterate over every row in a TSV file and import each as a compound document.
    We don't yet create edges for compounds.
    """
    with open(in_file_path, newline='') as csv_fd:
        reader = csv.reader(csv_fd, delimiter=' ', quotechar='"')
        with open(out_json_file_path, "w") as out_j:
            for row in reader:
                if (row[0] != "#"):
                    doc = {
                        '_from': _reaction_vert_name + '/' + row[0],
                        '_to': _reaction_vert_name + '/' + row[1],
                        'sf_similarity': float(row[2]),
                        'df_similarity': float(row[3])
                    }
                    out_j.write(json.dumps(doc) + "\n")


if __name__ == '__main__':
    """
    Simple command-line API:
    python arangodb_biochem_importer/import_reaction_similarities.py <path-to-file>
    """
    start = int(time.time() * 1000)
    if len(sys.argv) < 2:
        sys.stderr.write('Provide input file path of a csv containing similarity data and output json file path\n')
        exit(1)

    in_file_path = os.path.abspath(sys.argv[1])
    out_json_file_path = os.path.abspath(sys.argv[2])
    if not os.path.exists(in_file_path):
        sys.stderr.write('%s does not exist\n' % in_file_path)
        exit(1)
    convert_similarities(in_file_path, out_json_file_path)
    print('total running time in ms: %d' % (int(time.time() * 1000) - start))
