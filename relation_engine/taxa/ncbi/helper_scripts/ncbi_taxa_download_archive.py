#!/usr/bin/env python

# Downloads all the NCBI tax dumps from the ftp site. Does not download the new_taxdump* archives.
# use -h for help.

# Tested manually. Be sure to retest if you make changes.

from ftplib import FTP
import pathlib
import argparse
NCBI_HOST = 'ftp.ncbi.nih.gov'
NCBI_TAX_DIR = '/pub/taxonomy/taxdump_archive/'
TAXDUMP_PREFIX = 'taxdmp_'


def parseargs():
    parser = argparse.ArgumentParser(
        description='Download the entire NCBI Taxonomy archives.')
    parser.add_argument('--dir', required=True,
                        help='the directory in which to store the files')

    return parser.parse_args()


def download_if_missing(ftp, directory, filename):
    zf = pathlib.Path(directory) / filename
    if (zf.exists()):
        print(f'Skipping {zf}, file already exists')
        return
    with open(zf, 'wb') as f:
        print(f'Downloading {zf}')
        ftp.retrbinary(f'RETR {filename}', lambda block: f.write(block))


def main():
    a = parseargs()
    pathlib.Path(a.dir).mkdir(parents=True, exist_ok=True)

    with FTP(NCBI_HOST) as ftp:
        ftp.login()
        ftp.cwd(NCBI_TAX_DIR)
        for f in ftp.mlsd(facts=['size']):
            if f[0].startswith(TAXDUMP_PREFIX):
                download_if_missing(ftp, a.dir, f[0])


if __name__ == '__main__':
    main()
