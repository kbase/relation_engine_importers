#!/usr/bin/python3

# this script takes one argument, the directory which contains two NCBI taxdump
# files names.dmp and nodes.dmp.  It then creates two JSON files for uploading
# into Arango:
#       ncbi_taxon.json
#       ncbi_child_of_taxon.json

import json
import os
import re
import sys


if len(sys.argv) < 2:
    print("supply unzipped NCBI taxdump directory name for loading")
    sys.exit(1)

dirname = sys.argv[1]

taxon_collection_name = "ncbi_taxon"
vertices_json_file_name = taxon_collection_name + ".json"
edges_json_file_name = "ncbi_child_of_taxon.json"


print("Loading from {0} ...".format(dirname))


def load_names(file):
    print("Loading {0}".format(file))
    name_table = {}
    with open(file) as nf:
        for line in nf:
            tax_id, name, unique_name, category = re.split(r'\s\|\s?', line)[0:4]
            if tax_id not in name_table:
                name_table[tax_id] = {}
            if category not in name_table[tax_id]:
                name_table[tax_id][category] = []
            name_table[tax_id][category].append(name)

    return(name_table)


name_table = load_names(os.path.join(dirname, "names.dmp"))

taxa = []
edges = []

# read and process nodes file


def canonicalize(str):

    ret = []
    for x in re.split(r'\s+', re.sub("[^a-z]", " ", str.lower()).strip()):
        if x not in ["et", "al", "and", "or", "the", "a"]:
            ret.append(x)
    return(ret)


with open(os.path.join(dirname, "nodes.dmp")) as f:
    for line in f:
        record = re.split(r'\s\|\s?', line)
        id, parent, rank, gencode = [record[i] for i in [0, 1, 2, 6]]
        # print( id, parent, rank, gencode )

        aliases = []
        for cat in list(name_table[id].keys()):
            if cat != "scientific name":
                for nam in name_table[id][cat]:
                    aliases.append({"category":  cat,
                                    "name":      nam,
                                    "canonical": canonicalize(nam)})

        # vertex

        sci_name = name_table[id]["scientific name"][0]
        taxa.append(
            {"_key":                       id,
             "scientific_name":            sci_name,
             "canonical_scientific_name":  canonicalize(sci_name),
             "rank":                       rank,
             "aliases":                    aliases,
             "NCBI_taxon_id":              int(id),
             "gencode":                    gencode
             }
        )

        # edge

        edges.append(
            {"_from":       taxon_collection_name + "/" + id,
             "_to":         taxon_collection_name + "/" + parent,
             "child_type":  "t"
             }
        )

# this writes the whole list as a JSON list for Aardvark
# def write_json_from_list( filename, l ):
#    with open( filename, "w" ) as out:
#        out.write( json.dumps( l ) )
#    print( "written: {0}".format( filename ) )

# this version writes as individual lines for RE API uploading
# (https://github.com/kbase/relation_engine_api)


def write_json_from_list(filename, l):
    with open(filename, "w") as out:
        for r in l:
            out.write(json.dumps(r) + "\n")
    print("written: {0}".format(filename))


write_json_from_list(vertices_json_file_name, taxa)

write_json_from_list(edges_json_file_name, edges)
