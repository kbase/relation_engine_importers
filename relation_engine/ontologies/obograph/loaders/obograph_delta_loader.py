#!/usr/bin/env python

# TODO TEST

# TODO add version command line option (see ncbi loader)
# TODO switch from 10+ args to a config file (see ncbi loader)

import argparse
import getpass
import json
from arango import ArangoClient

from relation_engine.ontologies.obograph.parsers import OBOGraphLoader
from relation_engine.batchload.delta_load import load_graph_delta
from relation_engine.batchload.time_travelling_database import ArangoBatchTimeTravellingDB


def parse_args():
    parser = argparse.ArgumentParser(description="""
Load a OBOGraph ontology file into an ArangoDB time travelling database, calculating and applying
the changes between the prior load and the current load, and retaining the prior load.
""".strip())
    parser.add_argument('--file', required=True, help='the OBOGraph file')
    parser.add_argument(
        '--onto-id-prefix',
        required=True,
        help='the prefix of the ontology IDs in this load, e.g. GO, ENVO')
    parser.add_argument(
        '--arango-url',
        required=True,
        help='The url of the ArangoDB server (e.g. http://localhost:8528')
    parser.add_argument(
        '--database',
        required=True,
        help='the name of the ArangoDB database that will be altered')
    parser.add_argument(
        '--user',
        help='the ArangoDB user name; if --pwd-file is not included a password prompt will be ' +
        'presented. Omit to connect with default credentials.')
    parser.add_argument(
        '--pwd-file',
        help='the path to a file containing the ArangoDB password and nothing else; ' +
        'if --user is included and --pwd-file is omitted a password prompt will be presented.')
    parser.add_argument(
        '--load-namespace',
        required=True,
        help='the name of the data that is being loaded, e.g. envo, gene_ontology, etc. ' +
        'Must be unique across all load sources and consistent across loads.')
    parser.add_argument(
        '--load-registry-collection',
        required=True,
        help='the name of the ArangoDB collection where the load will be registered. ' +
        'This is typically the same collection for all delta loaded data.')
    parser.add_argument(
        '--node-collection',
        required=True,
        help='the name of the ArangoDB collection into which ontology nodes will be loaded')
    parser.add_argument(
        '--edge-collection',
        required=True,
        help='the name of the ArangoDB collection into which ontology edges will be loaded')
    parser.add_argument(
        '--merge-edge-collection',
        required=True,
        help='the name of the ArangoDB collection into which merge edges will be loaded')
    parser.add_argument(
        '--load-version',
        required=True,
        help='the version of this load. This version will be added to a field in the nodes and ' +
             'edges and will be used as part of the _key field.')
    parser.add_argument(
        '--load-timestamp',
        type=int,
        required=True,
        help='the timestamp to be applied to the load, in unix epoch milliseconds. Any nodes ' +
             'or edges created in this load will start to exist with this time stamp. ' +
             'NOTE: the user is responsible for ensuring this timestamp is greater than any ' +
             'other timestamps previously used to load data into the NCBI taxonomy DB.')
    parser.add_argument(
        '--release-timestamp',
        type=int,
        required=True,
        help='the timestamp, in unix epoch milliseconds, when the data was released ' +
        'at the source.')
    parser.add_argument(
        '--graph-id',
        help='if there are multiple graphs in the OBOGraph file, specify the full ID of the ' +
        'graph to be processed. If there is only one graph this flag may be omitted.')

    return parser.parse_args()


def main():
    a = parse_args()
    client = ArangoClient(hosts=a.arango_url)
    if a.user:
        if a.pwd_file:
            with open(a.pwd_file) as pwd_file:
                pwd = pwd_file.read().strip()
        else:
            pwd = getpass.getpass()
        db = client.db(a.database, a.user, pwd, verify=True)
    else:
        db = client.db(a.database, verify=True)
    attdb = ArangoBatchTimeTravellingDB(
        db,
        a.load_registry_collection,
        a.node_collection,
        default_edge_collection=a.edge_collection,
        merge_collection=a.merge_edge_collection)

    with open(a.file) as f:
        obograph = json.loads(f.read())

    loader = OBOGraphLoader(obograph, a.onto_id_prefix, graph_id=a.graph_id)

    load_graph_delta(
        a.load_namespace,
        loader.get_node_provider(),
        loader.get_edge_provider(),
        attdb,
        a.load_timestamp,
        a.release_timestamp,
        a.load_version,
        merge_source=loader.get_merge_provider())


if __name__ == '__main__':
    main()
