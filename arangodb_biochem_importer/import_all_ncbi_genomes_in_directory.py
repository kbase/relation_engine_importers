import re
import sys
import os
import time

from import_ncbi_genome import import_genomes, setup


def main():
    start = int(time.time() * 1000)
    if not len(sys.argv) >= 2:
        sys.stderr.write('Pass in the directory path of many subdirectories containing genbank files.\n')
        sys.exit(1)
    parent_dir = sys.argv[1]
    if not os.path.isdir(parent_dir):
        sys.stderr.write('The parent directory %s does not exist\n' % parent_dir)
        sys.exit(1)
    setup()
    failures = []  # type: list
    for subdir in os.listdir(parent_dir):
        if not re.search(r'GCF_\d\d\d\d\d\d\d\d\d\.\d', subdir):
            # Subdirectory must match GCF accession ID format
            continue
        full_path = os.path.join(parent_dir, subdir)
        print('importing genome in %s' % subdir)
        try:
            import_genomes(full_path)
        except Exception as err:
            failures.append(str(err))
        print('  done importing %s' % subdir)
    # Write failed imports out to a log file
    failures_file_path = os.path.join(parent_dir, 'failures.log')
    with open(failures_file_path, 'w') as fd_write:
        fd_write.write('\n'.join(failures))
    print('wrote failed imports to %s' % failures_file_path)
    end = int(time.time() * 1000)
    print('total time running in ms: %s' % (end - start))


if __name__ == '__main__':
    main()
