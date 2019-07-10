#!/bin/bash

rm -rf example_data/import_data
mkdir example_data/import_data

python arangodb_biochem_importer/generate_genome_import_data.py \
  example_data/test_output \
  example_data/import_data \

cat import_all_ncbi_genomes_in_directory.log
echo '--------------'

python arangodb_biochem_importer/import_json_data.py example_data/import_data
cat import_json_data.log
