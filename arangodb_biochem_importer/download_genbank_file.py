import re
import os
from Bio import Entrez
import tempfile


def download_genbank_file(accession_id, email):
    """
    Download a genbank file from an accesion ID such as GCF_1234.1
    """
    Entrez.email = email
    is_valid_id = bool(re.search(r'GCF_\d\d\d\d\d\d\d\d\d\.\d', accession_id))
    if not is_valid_id:
        raise ValueError('Invalid genome ID "%s", should have the format GCF_NNNNNNNNN.N')
    print('Searching...')
    handle = Entrez.esearch(db="nucleotide", term=accession_id + '[ALL]')
    record = Entrez.read(handle)
    handle.close()
    if not record.get('IdList'):
        raise ValueError('Invalid search results: ' + str(record))
    tmpdir = tempfile.mkdtemp()
    # The first id will be the chromosome sequence
    for genome_id in record['IdList']:
        print('Downloading genome with ID ' + genome_id)
        handle = Entrez.efetch(db='nuccore', id=genome_id, rettype='gbwithparts', retmode='text')
        file_path = os.path.join(tmpdir, genome_id + '.gb')
        with open(file_path, 'w') as fd_write:
            for chunk in handle.read():
                fd_write.write(chunk)
        handle.close()
        print('\nsuccess! finished writing ' + file_path)
    return tmpdir
