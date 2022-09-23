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
from relation_engine.version import VERSION

_BAC_INPUT_FILE = 'bac_input_file'
_AR_INPUT_FILE = 'ar_input_file'
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
    parser.add_argument('--version', action='version', version=VERSION)
    a = parser.parse_args()
    with open(a.config, 'rb') as c:
        return DeltaLoaderConfig(c, [_BAC_INPUT_FILE, _AR_INPUT_FILE])


def main():
    cfg = get_config()
    client = ArangoClient(hosts=cfg.url)
    if cfg.username:
        db = client.db(cfg.database, cfg.username, cfg.password, verify=True)
    else:
        db = client.db(cfg.database, verify=True)
    attdb = ArangoBatchTimeTravellingDB(
        db,
        cfg.load_registry_collection,
        cfg.node_collection,
        default_edge_collection=cfg.edge_collection)

    bif = cfg.inputs[_BAC_INPUT_FILE]
    aif = cfg.inputs[_AR_INPUT_FILE]
    with open(bif) as bin1, open(bif) as bin2, open(aif) as ain1, open(aif) as ain2:
        nodeprov = GTDBNodeProvider(bin1, ain1)
        edgeprov = GTDBEdgeProvider(bin2, ain2)

        load_graph_delta(_LOAD_NAMESPACE, nodeprov, edgeprov, attdb,
                         cfg.load_timestamp, cfg.release_timestamp, cfg.load_version)


if __name__ == '__main__':
    main()
