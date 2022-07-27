#!/bin/bash

# See https://www.kegg.jp/kegg/rest/keggapi.html
# Use the KEGG API to download lists of reactions/compounds/orthologs
# Then use the KEGG API to download entries of reactions/compounds/orthologs, 10 at a time

set -x  # print commands before executing

REPO_DIR=$(git rev-parse --show-toplevel)
DATA_DIR=$REPO_DIR/data/$(basename $(dirname $(realpath $0)))/
KEGG_CPD_URL=http://rest.kegg.jp/list/compound
KEGG_RXN_URL=http://rest.kegg.jp/list/reaction
KEGG_ORT_URL=http://rest.kegg.jp/list/ko
KEGG_ENZ_URL=http://rest.kegg.jp/list/enzyme
KEGG_EC_HIER_URL="https://www.genome.jp/brite/htext=ko01000&selected=none&extend=D3268D3297D4037"


if [[ ! -e $DATA_DIR ]]; then
    mkdir -p $DATA_DIR
fi

KEGG_CPD_FP=$DATA_DIR/$(basename $KEGG_CPD_URL).tsv
KEGG_RXN_FP=$DATA_DIR/$(basename $KEGG_RXN_URL).tsv
KEGG_ORT_FP=$DATA_DIR/$(basename $KEGG_ORT_URL).tsv
KEGG_ENZ_FP=$DATA_DIR/$(basename $KEGG_ENZ_URL).tsv
KEGG_EC_HIER_FP=$DATA_DIR/ec_hier.json

#curl --location $KEGG_CPD_URL > $KEGG_CPD_FP
#curl --location $KEGG_RXN_URL > $KEGG_RXN_FP
#curl --location $KEGG_ORT_URL > $KEGG_ORT_FP
curl --location $KEGG_ENZ_URL > $KEGG_ENZ_FP
curl --location $KEGG_EC_HIER_URL > $KEGG_EC_HIER_FP

# For compound, reaction, ko, enzyme, get full files
#python -m download_kegg $DATA_DIR $KEGG_CPD_FP $KEGG_RXN_FP $KEGG_ORT_FP $KEGG_ENZ_FP
python -m download_kegg $DATA_DIR $KEGG_ENZ_FP
