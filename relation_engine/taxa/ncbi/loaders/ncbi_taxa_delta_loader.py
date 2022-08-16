#!/usr/bin/env python

# TODO TEST
# for now tested manually

import argparse
from arango import ArangoClient

from relation_engine.taxa.config import DeltaLoaderConfig
from relation_engine.taxa.ncbi.parsers import NCBINodeProvider
from relation_engine.taxa.ncbi.parsers import NCBIEdgeProvider
from relation_engine.taxa.ncbi.parsers import NCBIMergeProvider
from relation_engine.batchload.delta_load import load_graph_delta
from relation_engine.batchload.time_travelling_database import ArangoBatchTimeTravellingDB

_LOAD_NAMESPACE = 'ncbi_taxa'
_INPUT_DIRECTORY = 'input_directory'

NAMES_IN_FILE = 'names.dmp'
NODES_IN_FILE = 'nodes.dmp'
MERGED_IN_FILE = 'merged.dmp'


def get_config():
    parser = argparse.ArgumentParser(description="""
Load a NCBI taxonomy dump into an ArangoDB time travelling database, calculating and applying the
changes between the prior load and the current load, and retaining the prior load.
""".strip())
    parser.add_argument('--config', required=True,
                        help='the path to the loader configuration file. NOTE: the config '
                        + 'file will need to be updated for each consecutive load; it is not '
                        + 'static.')
    a = parser.parse_args()
    with open(a.config, 'rb') as c:
        return DeltaLoaderConfig(c, [_INPUT_DIRECTORY], require_merge_collection=True)


def main():
    cfg = get_config()
    rootdir = cfg.inputs[_INPUT_DIRECTORY]
    nodes = rootdir / NODES_IN_FILE
    names = rootdir / NAMES_IN_FILE
    merged = rootdir / MERGED_IN_FILE
    client = ArangoClient(hosts=cfg.url)
    if cfg.username:
        db = client.db(cfg.database, cfg.username, cfg.password, verify=True)
    else:
        db = client.db(cfg.database, verify=True)
    attdb = ArangoBatchTimeTravellingDB(
        db,
        cfg.load_registry_collection,
        cfg.node_collection,
        default_edge_collection=cfg.edge_collection,
        merge_collection=cfg.merge_edge_collection)

    with open(nodes) as in1, open(names) as namesfile, open(nodes) as in2, open(merged) as merge:
        nodeprov = NCBINodeProvider(namesfile, in1)
        edgeprov = NCBIEdgeProvider(in2)
        merge = NCBIMergeProvider(merge)

        load_graph_delta(_LOAD_NAMESPACE, nodeprov, edgeprov, attdb,
                         cfg.load_timestamp, cfg.release_timestamp, cfg.load_version,
                         merge_source=merge)


if __name__ == '__main__':
    main()
