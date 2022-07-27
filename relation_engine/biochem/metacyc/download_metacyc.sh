#!/bin/bash

# Even though MetaCyc data files are free, you still need to contact SRI/BioCyc
# to get a free account to access the data files. Then you can manually download
# their tarball

set -x  # print commands before executing

REPO_DIR=$(git rev-parse --show-toplevel)
DATA_DIR=$REPO_DIR/data/$(basename $(dirname $(realpath $0)))/

if [[ ! -e $DATA_DIR ]]; then
    mkdir -p $DATA_DIR
fi
