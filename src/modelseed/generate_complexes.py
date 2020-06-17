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
import logging

from utils.parse_gpr import parse_gpr
from utils.flatten_boolean_expr import flatten_expr
from utils.write_import_file import write_multiple_import_files

log_file_path = sys.argv[0] + '.log'
logging.basicConfig(filename=log_file_path, filemode='w', level=logging.DEBUG)

source = "ModelSEED"    # goes into "source" field in rxn_gene_complex

have_gene_key = {}      # hash used to suppress duplicate keys in rxn_gene_complex

_reaction_vert_name = 'rxn_reaction'
_gene_vert_name = 'ncbi_gene'
_complex_vert_name = 'rxn_gene_complex'
_reaction_to_complex_edge_name = 'rxn_reaction_within_complex'
_gene_to_complex_edge_name = 'rxn_gene_within_complex'


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


def gen_complex_data(row, headers):
    """Import a single reaction from a row in a TSV file."""
    reaction = {}  # type: dict
    for (idx, col) in enumerate(row):
        reaction[headers[idx]] = col
    if '_key' not in reaction:
        return
    parsed_gpr = parse_gpr(reaction['gpr'])
    complexes = flatten_expr(parsed_gpr.value)
    if not complexes:
        return
    for cmplx in complexes:
        cmplx.sort()
        gene_count = len([x for x in cmplx if x != 'Unknown'])
        if gene_count == 0:
            continue
        complex_key = hashlib.blake2b(str(cmplx).encode(), digest_size=16).hexdigest()

        # suppressing yield of duplicate keys
        if not( complex_key in have_gene_key.keys() ): 
            gene_complex = {'genes': cmplx, '_key': complex_key, 'source': source}
            yield (_complex_vert_name, gene_complex)
        have_gene_key[complex_key] = True

        gene_complex_id = _complex_vert_name + '/' + complex_key
        reaction_id = _reaction_vert_name + '/' + reaction['_key']
        reaction_within_complex = {'_from': reaction_id, '_to': gene_complex_id}
        yield (_reaction_to_complex_edge_name, reaction_within_complex)
        # Import gene to complex link
        for locus_id in cmplx:
            if locus_id == 'Unknown':
                continue
            gene_id = _gene_vert_name + '/' + locus_id
            gene_within_complex = {'_from': gene_id, '_to': gene_complex_id}
            yield (_gene_to_complex_edge_name, gene_within_complex)


def iterate_tsv_rows(file_path):
    """
    Iterate over every row in a TSV file and import each as a reaction document.
    For each reaction, we create:
    - A reaction
    - A set of edges from the reaction to all constituent compounds
    - A set of gene complexes based on the 'gpr' boolean expression of required genes
    - Edges from the gene complexes to the genes
    - Edges from the gene complexes to the reaction that gets produced
    """
    with open(file_path, newline='') as csv_fd:
        reader = csv.reader(csv_fd, delimiter='\t', quotechar='"')
        headers = [header_transforms.get(h, h) for h in next(reader)]
        for row in reader:
            reaction_gen = gen_complex_data(row, headers)
            for result in reaction_gen:
                yield result


def get_reaction_files(dir_path):
    """Get all the reaction filepaths for a directory ('*reactions.tsv')"""
    file_pattern = r'.*reactions\.tsv'
    for file_name in os.listdir(dir_path):
        if re.search(file_pattern, file_name):
            # Yield the full path
            yield os.path.join(dir_path, file_name)


def iterate_reaction_dir(input_dir, output_dir):
    # Generate:
    # reactions, gene_complexes, reaction_within_complex, gene_within_complex
    for file_path in get_reaction_files(input_dir):
        # Writes out dir/rxn_gene_complex.json
        # Writes out dir/rxn_gene_within_complex.json
        # Writes out dir/rxn_reaction_within_complex.json
        write_multiple_import_files(iterate_tsv_rows(file_path), {
            _gene_to_complex_edge_name: os.path.join(output_dir, _gene_to_complex_edge_name + '.json'),
            _reaction_to_complex_edge_name: os.path.join(output_dir, _reaction_to_complex_edge_name + '.json'),
            _complex_vert_name: os.path.join(output_dir, _complex_vert_name + '.json'),
        })


if __name__ == '__main__':
    """
    Simple command-line API:
    python arangodb_biochem_importer/import_reactions.py <path-to-directory-of-reaction-files>

    Where all reaction files are TSVs with the file name '*reactions.tsv'
    """
    start = int(time.time() * 1000)
    if len(sys.argv) < 3:
        sys.stderr.write(
            'Pass in these args:\n'
            '- directory path containing tsv files of reaction data (with filenames "*reactions.tsv")\n'
            '- output directory path to save the importable json files\n'
        )
        exit(1)
    input_dir = sys.argv[1]
    if not os.path.isdir(input_dir):
        sys.stderr.write('%s is not a directory' % input_dir)
        sys.exit(1)
    output_dir = sys.argv[2]
    if not os.path.isdir(output_dir):
        print('%s does not exist, creating..' % output_dir)
        os.mkdir(output_dir)
    print('logging to %s' % log_file_path)
    iterate_reaction_dir(input_dir, output_dir)
    print('..done!')
