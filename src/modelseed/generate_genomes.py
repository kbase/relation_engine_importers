"""
Given a directory where...
- every subdirectory corresponds to an organism
- every subdirectory contains genbank files for the genomes of that organism (chromosome + plasmids)
Then...
- iterate over every genbank and parse it with biopython
- output importable CSV files in another output directory that can be used by ./import_csv_directory.py

This will output 2 importable csv files: 'genome.csv' and 'genes.csv'
These must not be present in the output directory that you provide
"""
import logging
import re
import sys
import os
import time

from generate_genome_helpers import generate_genome_import_files

log_file_path = 'import_all_ncbi_genomes_in_directory.log'
logging.basicConfig(filename=log_file_path, filemode='w', level=logging.DEBUG)

_genome_vert_name = 'ncbi_genome'
_gene_vert_name = 'ncbi_gene'
_gene_to_genome_edge_name = 'rxn_gene_within_genome'


def iterate_dirs(input_dir, output_dir):
    """
    Iterate over all subdirectories and import every genome.
    """
    for subdir in os.listdir(input_dir):
        logging.info('generating import data for %s' % subdir)
        # Subdirectory must match GCF accession ID format
        if not re.search(r'GCF_\d\d\d\d\d\d\d\d\d\.\d', subdir):
            logging.error('invalid subdirectory name %s\n' % subdir)
            continue
        full_path = os.path.join(input_dir, subdir)
        iterate_genbanks(full_path)


def iterate_genbanks(dir_path):
    """
    Iterate and generate import data for all genbank files within a directory.
    For each genome, we yield one row in output_dir/ncbi_genome.json
    And we create a gene import like output_dir/genome_id/ncbi_gene.json
    """
    for file_name in os.listdir(dir_path):
        full_path = os.path.join(dir_path, file_name)
        try:
            generate_genome_import_files(full_path, output_dir)
        except Exception as err:
            logging.error('failed to generate %s\t%s' % (dir_path, str(err)))


def check_dir(dir_path):
    """Check for a valid and present directory."""
    if not os.path.isdir(dir_path):
        sys.stderr.write('The directory %s does not exist\n' % dir_path)
        sys.exit(1)


if __name__ == '__main__':
    """
    Simple command-line interface:
        python import_all_ncbi_genomes_in_directory.py <input-dir> <output-dir>
    Produces importable CSVs in output-dir
    """
    if len(sys.argv) < 3:
        sys.stderr.write(
            'Pass in 2 required arguments:\n'
            '- parent directory path that contains many subdirectories containing genbank files\n'
            '- output directory where you want to save importable csv files\n'
        )
        sys.exit(1)
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    check_dir(input_dir)
    os.makedirs(output_dir, exist_ok=True)
    print('logging to %s' % log_file_path)
    start = int(time.time() * 1000)
    logging.info('starting run at %s' % start)
    iterate_dirs(input_dir, output_dir)
    end = int(time.time() * 1000)
    logging.info('total time running in ms: %s' % (end - start))
    print('.. done')
