#!/bin/bash
#
#  make sure DB_USER, DB_PASS and DB_URL are properly set as well
#  as BINDIR. then
#
#    bash  shell_load_directoy.py  JSONdirectory
# 
#  this first loads all rxn_*.json files into collections derived from
#  the filename, then loads all kegg_rxn_*.json, removing the kegg_
#  prefix to determine the collection name
#

shopt -s nullglob

BINDIR="./arangodb_biochem_importer/src/utils"
#BINDIR="./relation_engine_importers/src/utils"
LOADER="python $BINDIR/import_json_file.py "


JSON_DIR=$1

RFILES=$JSON_DIR/rxn_*.json
KFILES=$JSON_DIR/kegg_*.json


# handle generic reaction and ModelSEED collections first

for JFILE in $RFILES
do
    COLLECTION=$(basename $JFILE | sed -e 's/\.json$//')
    echo $LOADER -n $COLLECTION $JFILE
    $LOADER -n $COLLECTION $JFILE
done

# now append KEGG files to the existing collections

for JFILE in $KFILES
do
    COLLECTION=$(basename $JFILE | sed -e 's/^kegg_//' -e 's/\.json$//')
    echo $LOADER -n $COLLECTION $JFILE
    $LOADER -n $COLLECTION $JFILE
done

echo $0 finished.
    

