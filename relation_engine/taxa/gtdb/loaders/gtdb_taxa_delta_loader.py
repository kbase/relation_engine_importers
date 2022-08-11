#!/usr/bin/env python

# TODO TEST
# for now tested manually

import argparse
from arango import ArangoClient

from relation_engine.taxa.config import DeltaLoaderConfig
from relation_engine.taxa.gtdb.parsers import GTDBNodeProvider
from relation_engine.taxa.gtdb.parsers import GTDBEdgeProvider
from relation_engine.batchload.delta_load import load_graph_delta
from relation_engine.batchload.time_travelling_database import ArangoBatchTimeTravellingDB

_INPUT_FILE = 'input_file'
_LOAD_NAMESPACE = 'gtdb_taxa'


def get_config():
    parser = argparse.ArgumentParser(description="""
Load a GTDB taxonomy dump into an ArangoDB time travelling database, calculating and applying the
changes between the prior load and the current load, and retaining the prior load.
""".strip())
    parser.add_argument('--config', required=True,
                        help='the path to the loader configuration file. NOTE: the config '
                        + 'file will need to be updated for each consecutive load; it is not '
                        + 'static.')
    a = parser.parse_args()
    with open(a.config, 'rb') as c:
        return DeltaLoaderConfig(c, [_INPUT_FILE])


def main():
    cfg = get_config()
    client = ArangoClient(hosts=cfg.url)
    if cfg.user:
        db = client.db(cfg.database, cfg.user, cfg.password, verify=True)
    else:
        db = client.db(cfg.database, verify=True)
    attdb = ArangoBatchTimeTravellingDB(
        db,
        cfg.load_registry_collection,
        cfg.node_collection,
        default_edge_collection=cfg.edge_collection)

    input_file = cfg.inputs[_INPUT_FILE]
    with open(input_file) as in1, open(input_file) as in2:
        nodeprov = GTDBNodeProvider(in1)
        edgeprov = GTDBEdgeProvider(in2)

        load_graph_delta(_LOAD_NAMESPACE, nodeprov, edgeprov, attdb,
                         cfg.load_timestamp, cfg.release_timestamp, cfg.load_version)


if __name__ == '__main__':
    main()
