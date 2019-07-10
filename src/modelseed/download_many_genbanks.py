"""
Download a collection of genbank files into a series of directories
"""
import sys
import re
import os
from download_genbank_file import download_genbank_file


def get_all_accession_ids_from_directory(dir_path):
    """
    Given a directory of files wwith
    """
    ids = set()  # type: set
    pattern = r'.*(GCF_\d\d\d\d\d\d\d\d\d\.\d).*'
    for file_name in os.listdir(dir_path):
        matches = re.findall(pattern, file_name)
        ids = ids | set(matches)
    return ids


def download_genbanks_to_dir(accession_ids, parent_dir_path):
    """
    Download a list of accession IDs to a directory.

    We want to do this serially as NCBI has some strict restrictions.
    """
    email = os.environ['ENTREZ_EMAIL']
    fd_write = open(os.path.join(parent_dir_path, 'failures.log'), 'w')
    for acc_id in accession_ids:
        dir_path = os.path.join(parent_dir_path, acc_id)
        if os.path.isdir(dir_path):
            print('%s already exists, skipping...' % acc_id)
            continue
        else:
            os.mkdir(dir_path)
        try:
            download_genbank_file(acc_id, email, dir_path)
        except Exception:
            print('Encountered exception downloading %s' % acc_id)
            fd_write.write('Failed on %s\n' % acc_id)
    fd_write.close()
    return parent_dir_path


if __name__ == '__main__':
    if 'ENTREZ_EMAIL' not in os.environ:
        sys.stderr.write('Set the ENTREZ_EMAIL env var to your email for NCBI.\n')
        sys.exit(1)
    if len(sys.argv) < 3:
        sys.stderr.write('Pass in two command line arguments:\n')
        sys.stderr.write('  a path to a directory containing filenames which contain NCBI accession IDs\n')
        sys.stderr.write('  a path where you would like to save the downloaded genbank files.\n')
        sys.exit(1)
    file_name_path = sys.argv[1]
    output_dir = sys.argv[2]
    if not os.path.isdir(output_dir):
        print('Output directory %s does not exist. Creating it.' % output_dir)
        os.mkdir(output_dir)
    ids = get_all_accession_ids_from_directory(sys.argv[1])
    print('Downloading %s genomes' % len(ids))
    download_genbanks_to_dir(ids, output_dir)
