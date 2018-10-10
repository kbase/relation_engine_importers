import re
import sys
import os

from import_ncbi_genome import import_genomes


if __name__ == '__main__':
    if not len(sys.argv) >= 2:
        sys.stderr.write('Pass in the directory path with genome names')
        sys.exit(1)
    pattern = r'(GCF_\d\d\d\d\d\d\d\d\d\.\d)'
    ids = set()  # type: set
    for path in os.listdir(sys.argv[1]):
        found = re.findall(pattern, path)
        ids = ids | set(found)
    for gcf_id in ids:
        print('gcf_id', gcf_id)
        import_genomes(gcf_id)
