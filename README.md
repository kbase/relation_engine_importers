# Biochemistry data importer for ArangoDB

This is an experimental utility that imports genome and biochemistry data into an ArangoDB graph.

## Setup

Create a virtualenv or Conda env that uses Python 3.6+. With your environment active, install dependencies:

```sh
$ make install
# (This runs: pip install --extra-index-url https://pypi.anaconda.org/kbase/simple -r requirements.txt)
```

You can run the tests with:

```sh
$ make test
```

## Usage

Have a running ArangoDB server on `localhost:8529` (you can also use the env var "`DB_URL`").

You can set the following env vars when running:

```
DB_USERNAME (defaults to 'root')
DB_PASSWORD (defaults to 'password')
DB_NAME     (defaults to '_system')
DB_URL      (defaults to 'http://localhost:8529')
```

> All import actions are merge-based "upserts", meaning the entries are inserted if they don't exist, and are either updated or replaced if they already exist.

### Downloading genomes from NCBI

Given a directory full of filenames that contain NCBI assembly ids such as `GCF_000018105.1`, this
script will iterate over all of them and download all the genomes as genbank files in an output
directory. 

```sh
$ python ./arangodb_biochem_importer/download_many_genbanks.py \
    <path-to-directory-containing-filenames-with-ncbi-ids> \
    <path-to-output-directory>
```

All genbanks will be saved in the output directory inside subdirectories named after their
accession IDs. Each organism will likely have multiple genbank files in its subdirectory for
chromosomes plus all plasmids.

### Importing all genomes into the database

Given a directory of many genomes (the output of the NCBI download above), run this script to
import all the taxa, genomes, and genes into the database:

```sh
$ python ./arangodb_biochem_importer/import_all_ncbi_genomes_in_directory.py \
    <path-to-directory-of-downloaded-genomes>
```

### Importing compounds and reactions

Given a directory with TSV files (all named `xyz-reactions.tsv` or `xyz-compounds.tsv`), this
script will import them all into the arango db, creating `gene_complexes`, `reactions`, 
`compounds`, and connect them to existing genes (**you will want to run the genome/gene import
above before you run this import**).

```sh
$ python ./arangodb_biochem_importer/import_compounds.py <path-to-reactions-directory>
```

```sh
$ python ./arangodb_biochem_importer/import_reactions.py <path-to-reactions-directory>
```

### Importing reaction similarities

Given a TSV file with columns for `reaction_id1, reaction_id2, similarity_score`, this will import
`reaction_similar_to` edges for every row:

```sh
$ python ./arangodb_biochem_importer/import_reaction_similarities.py <path-to-tsv-file>
```
