"""
Iterate over a directory of TSV files, finding all named '*reactions.tsv', and import the data into
the database

A reaction data TSV has the following headers:
id, direction, compartment, gpr, name, enzyme, deltag, reference, equation, definition, ms id, bigg
id, kegg id, kegg pathways, metacyc pathways

A sample set of data for a single reaction (header: value)
  id: rxn02282_c0
  direction: = (can be <, >, or =)
  compartment: Cytosol_0
  gpr: (Unknown and (b2341 or b3846)) or (b2341 or b3846)
  name: N-Formimino-L-aspartate iminohydrolase_c0
  enzyme: 4.1.1.49
  deltag: 2.82
  reference:  (always blank)
  equation: (1)cpd00001[c0] + (1)cpd02154[c0] <=> (1)cpd00013[c0] + (1)cpd00769[c0]
  definition: (1)H2O_c0[c0] + (1)N-Formimino-L-aspartate_c0[c0] <=> (1)NH3_c0[c0] + (1)N-Formyl-L-aspartate_c0[c0]
  ms id: rxn02282
  bigg id: DHPS2
  kegg id: R03188
  kegg pathways: Histidine metabolism
  metacyc pathways:
    ALL-CHORISMATE-PWY|Biosynthesis|Cofactor-Biosynthesis|FOLSYN-PWY|Folate-Biosynthesis|Vitamin-Biosynthesis

Notes on each reaction field:
  gpr: gene complex and gets factored out into a list of and statements (eliminating 'or'). We
    ignore any conjunctions that have an 'Unknown' in them.
  equation and reference should be the same, with equation giving the compound id
"""
import time
import sys
import os
import re
import csv
import pprint

from init_db import init_db
from setup_collections import setup_collections
from parse_gpr import parse_gpr
from flatten_boolean_expr import flatten_boolean_expr

pp = pprint.PrettyPrinter(indent=2)


# Transformations on the header names
# Eg. given a header "id", save it as a field named "_key" in the db
header_transforms = {
    'id': 'identifier',
    'ms id': '_key',
    'kegg id': 'kegg_id',
    'bigg id': 'bigg_id',
    'kegg pathways': 'kegg_pathways',
    'metacyc pathways': 'metacyc_pathways'
}


def setup():
    """Initialize the db connection and collections and return the connection."""
    db = init_db()
    vertices = ['reactions', 'gene_complexes']
    edges = ['complex_has_gene', 'complex_produces_reaction']
    setup_collections(db, vertices, edges)
    return db


def import_reactions(file_path):
    """
    Iterate over every row in a TSV file and import each as a reaction document.
    For each reaction, we create:
    - A reaction
    - A set of edges from the reaction to all constituent compounds
    - A set of gene complexes based on the 'gpr' boolean expression of required genes
    - Edges from the gene complexes to the genes
    - Edges from the gene complexes to the reaction that gets produced
    """
    reactions = db.collections['reactions']
    print('reactions collection', reactions)
    with open(file_path, newline='') as csv_fd:
        reader = csv.reader(csv_fd, delimiter='\t', quotechar='"')
        headers = [
            header_transforms.get(h, h)
            for h in next(reader)
        ]
        to_insert = []
        for row in reader:
            row_data = {}  # type: dict
            to_insert.append(row_data)
            for (idx, col) in enumerate(row):
                row_data[headers[idx]] = col
            parsed_gpr = parse_gpr(row_data['gpr'])
            # a and b -> a+b
            # a or b -> a, b
            # a and (b or c) -> a and b, a and c
            # a or (b and c) -> a, b and c
            print('---')
            print('---')
            print('flattened', flatten_boolean_expr(parsed_gpr.value))
            print('---')
            print('original', parsed_gpr.value)
    # result = reactions.bulkSave(to_insert, onDuplicate="update")
    result = 'todo'
    return result


def get_reaction_files(dir_path):
    """Get all the reaction filepaths for a directory ('*reactions.tsv')"""
    file_pattern = r'.*reactions\.tsv'
    for file_name in os.listdir(dir_path):
        if re.search(file_pattern, file_name):
            # Yield the full path
            yield os.path.join(dir_path, file_name)


if __name__ == '__main__':
    """
    Simple command-line API:
    python arangodb_biochem_importer/import_reactions.py <path-to-directory-of-reaction-files>

    Where all reaction files are TSVs with the file name '*reactions.tsv'
    """
    start = int(time.time() * 1000)
    if len(sys.argv) <= 1:
        sys.stderr.write('Provide the directory path containing *reactions.tsv files.')
        exit(1)
    db = setup()
    reactions_dir = os.path.abspath(sys.argv[1])
    for file_path in get_reaction_files(reactions_dir):
        print('importing from tsv file %s' % file_path)
        result = import_reactions(file_path)
        print('Saved reactions', result)
    print('total running time in ms: %d' % (int(time.time() * 1000) - start))
