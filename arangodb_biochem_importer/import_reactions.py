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
import hashlib

from init_db import init_db
from setup_collections import setup_collections
from parse_gpr import parse_gpr
from flatten_boolean_expr import flatten_expr, remove_unknowns

db = init_db()


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
    vertices = ['reactions', 'gene_complexes']
    edges = ['complex_has_gene', 'complex_produces_reaction', 'reaction_has_compound']
    setup_collections(db, vertices, edges)
    return db


def import_reaction(row, headers):
    """Import a single reaction from a row in a TSV file."""
    doc = {}  # type: dict
    for (idx, col) in enumerate(row):
        doc[headers[idx]] = col
    # Insert the reaction document into `reactions`
    print('importing reaction %s' % doc['_key'])
    match = {'_key': doc['_key']}
    query = "UPSERT @match INSERT @doc REPLACE @doc IN reactions RETURN NEW"
    results = db.AQLQuery(query, bindVars={'doc': doc, 'match': match})
    reaction_id = results[0]['_id']
    print('  upserted %s' % results[0]['_id'])
    parsed_gpr = parse_gpr(doc['gpr'])
    complexes = remove_unknowns(flatten_expr(parsed_gpr.value))
    if not complexes:
        print('no gene complexes. continuing..')
        return
    import_gene_complexes(complexes, reaction_id)
    compound_equation = doc['equation']
    import_compound_edges(compound_equation, reaction_id)


def import_gene_complexes(complexes, reaction_id):
    """Import the gene complex for a reaction and all of its edges."""
    # Insert the gene_complex document
    genes = db.collections['genes']
    complexes_str = str(complexes)
    complexes_key = hashlib.blake2b(complexes_str.encode()).hexdigest()
    print('importing gene_complex %s' % complexes_str)
    doc = {'conjunctions': complexes, '_key': complexes_key}
    match = {'_key': complexes_key}
    query = "UPSERT @match INSERT @doc REPLACE @doc IN gene_complexes RETURN NEW"
    results = db.AQLQuery(query, bindVars={'doc': doc, 'match': match})
    gene_complex_id = results[0]['_id']
    print('  upserted %s' % gene_complex_id)
    # Import an edge between the gene complex and the reaction
    print('importing edges among genes, gene_complex, and reaction')
    doc = {'_from': gene_complex_id, '_to': reaction_id}
    query = "UPSERT @doc INSERT @doc REPLACE @doc IN complex_produces_reaction RETURN NEW"
    results = db.AQLQuery(query, bindVars={'doc': doc})
    print('  upserted %s', results[0]['_id'])
    # Import gene to complex link
    for comp in complexes:
        for locus_id in comp:
            gene_id = genes.name + '/' + locus_id
            doc = {'_from': gene_complex_id, '_to': gene_id}
            query = "UPSERT @doc INSERT @doc REPLACE @doc IN complex_has_gene RETURN NEW"
            results = db.AQLQuery(query, bindVars={'doc': doc})
            print('  upserted %s', results[0]['_id'])


def import_compound_edges(equation, reaction_id):
    """
    Import all `reaction_has_compound` edges between a reaction and its compounds.
    """
    compounds = db.collections['compounds']
    keys = re.findall(r'cpd\d\d\d\d\d', equation)
    print('importing reaction to compound edges')
    for key in keys:
        compound_id = compounds.name + '/' + key
        doc = {'_from': reaction_id, '_to': compound_id}
        query = "UPSERT @doc INSERT @doc REPLACE @doc IN reaction_has_compound RETURN NEW"
        results = db.AQLQuery(query, bindVars={'doc': doc})
        print('  upserted %s' % results[0]['_id'])


def import_reactions_from_tsv(file_path):
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
        headers = [header_transforms.get(h, h) for h in next(reader)]
        for row in reader:
            import_reaction(row, headers)
    result = 'todo'
    return result


def import_reactions_dir(dir_path):
    """Import many reactions for many genomes from a directory of TSV files."""
    reactions_dir = os.path.abspath(dir_path)
    for file_path in get_reaction_files(reactions_dir):
        print('importing from tsv file %s' % file_path)
        result = import_reactions_from_tsv(file_path)
        print('Saved reactions', result)


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
    setup()
    if len(sys.argv) <= 1:
        sys.stderr.write('Provide the directory path containing *reactions.tsv files.')
        exit(1)
    import_reactions_dir(sys.argv[1])
