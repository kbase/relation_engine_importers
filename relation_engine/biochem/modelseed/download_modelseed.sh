#!/bin/bash

# From the ModelSEED GitHub repository (https://github.com/ModelSEED/ModelSEEDDatabase)
# download the compound/reaction TSVs and READMEs into the $REPO_DIR

set -x  # print commands before executing

REPO_DIR=$(git rev-parse --show-toplevel)
DATA_DIR=$REPO_DIR/data/$(basename $(dirname $(realpath $0)))/
MODELSEED_CPD_URL=https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv
MODELSEED_RXN_URL=https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv
MODELSEED_CPD_README_URL=https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/COMPOUNDS.md
MODELSEED_RXN_README_URL=https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/REACTIONS.md


if [[ ! -e $DATA_DIR ]]; then
    mkdir -p $DATA_DIR
fi

curl --location $MODELSEED_CPD_URL > $DATA_DIR/$(basename $MODELSEED_CPD_URL)
curl --location $MODELSEED_RXN_URL > $DATA_DIR/$(basename $MODELSEED_RXN_URL)
curl --location $MODELSEED_CPD_README_URL > $DATA_DIR/$(basename $MODELSEED_CPD_README_URL)
curl --location $MODELSEED_RXN_README_URL > $DATA_DIR/$(basename $MODELSEED_RXN_README_URL)
