#!/bin/bash


set -x  # print commands before executing

REPO_DIR=$(git rev-parse --show-toplevel)
DATA_DIR=$REPO_DIR/data/$(basename $(dirname $(realpath $0)))/
CHEBI_ONT_DIR_URL=https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/
CHEBI_TSV_DIR_URL=https://ftp.ebi.ac.uk/pub/databases/chebi/Flat_file_tab_delimited/

if [[ ! -e $DATA_DIR ]]; then
    mkdir -p $DATA_DIR
fi

wget --recursive --no-clobber --convert-links $CHEBI_ONT_DIR_URL
