#!/bin/bash

set -x  # print commands before executing

# Get RHEA tarball


REPO_DIR=$(git rev-parse --show-toplevel)
DATA_DIR=$REPO_DIR/data/$(basename $(dirname $(realpath $0)))/  # repo/data/rhea
URL=https://ftp.expasy.org/databases/rhea/tsv/rhea-tsv.tar.gz
TARBALL_FP=$DATA_DIR/$(basename $URL)

if [[ ! -e $DATA_DIR ]]; then
    mkdir -p $DATA_DIR
fi

curl --location $URL > $TARBALL_FP
tar -vxf $TARBALL_FP -C $DATA_DIR
