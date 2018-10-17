import re
import sys
import os
import time

import import_ncbi_genome as importer


def main(parent_dir):
    failures_log_path = os.path.join(parent_dir, 'failures.log')
    failures_log = open(failures_log_path, 'w')
    import_count = 0
    for subdir in os.listdir(parent_dir):
        if not re.search(r'GCF_\d\d\d\d\d\d\d\d\d\.\d', subdir):
            failures_log.write('Invalid subdirectory name %s\n' % subdir)
            # Subdirectory must match GCF accession ID format
            continue
        full_path = os.path.join(parent_dir, subdir)
        print('importing genome in %s' % subdir)
        try:
            importer.import_genomes(full_path)
        except Exception as err:
            failures_log.write('Failed to import %s\t%s' % (subdir, str(err)))
    print('successfully imported %s genomes' % import_count)
    print('wrote failed imports to %s' % failures_log_path)
    failures_log.close()


if __name__ == '__main__':
    if not len(sys.argv) >= 2:
        sys.stderr.write('Pass in the directory path with many subdirectories containing genbank files.\n')
        sys.exit(1)
    parent_dir = sys.argv[1]
    if not os.path.isdir(parent_dir):
        sys.stderr.write('The parent directory %s does not exist\n' % parent_dir)
        sys.exit(1)
    print('running..')
    importer.setup()
    start = int(time.time() * 1000)
    main(parent_dir)
    end = int(time.time() * 1000)
    print('total time running in ms: %s' % (end - start))
