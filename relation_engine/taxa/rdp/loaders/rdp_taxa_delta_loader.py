#!/usr/bin/env python

# TODO TEST

# TODO add version command line option (see ncbi loader)
# TODO switch from 10+ args to a config file (see ncbi loader)

import argparse
import getpass
import gzip
from contextlib import ExitStack
from arango import ArangoClient

from relation_engine.taxa.rdp.parsers import RDPNodeProvider
from relation_engine.taxa.rdp.parsers import RDPEdgeProvider
from relation_engine.batchload.delta_load import load_graph_delta
from relation_engine.batchload.time_travelling_database import ArangoBatchTimeTravellingDB

# TODO probably should make some sort of general arg parser since they're all so similar

_LOAD_NAMESPACE = 'rdp_taxa'


def parse_args():
    parser = argparse.ArgumentParser(description=(
        "Load one or more RDP taxonomy dump files into an ArangoDB time travelling database, "
        "calculating and applying the changes between the prior load and the current load, and "
        "retaining the prior load."))
    parser.add_argument('--file-16S', action='append',
                        help='a RDP taxonomy gzipped FASTA file containing 16S data, e.g. ' +
                        'current_Bacteria_unaligned.fa.gz. This option may be specified ' +
                        'more than once.')
    parser.add_argument('--file-28S', action='append',
                        help='a RDP taxonomy gzipped FASTA file containing 28S data, e.g. ' +
                        'current_Fungi_unaligned.fa.gz. This option may be specified ' +
                        'more than once.')
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
        '--load-registry-collection',
        required=True,
        help='the name of the ArangoDB collection where the load will be registered. ' +
        'This is typically the same collection for all delta loaded data.')
    parser.add_argument(
        '--node-collection',
        required=True,
        help='the name of the ArangoDB collection into which taxa nodes will be loaded')
    parser.add_argument(
        '--edge-collection',
        required=True,
        help='the name of the ArangoDB collection into which taxa edges will be loaded')
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

    return parser.parse_args()


def main():
    a = parse_args()
    if not a.file_16S and not a.file_28S:
        raise ValueError('no input files were supplied')
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
        default_edge_collection=a.edge_collection)

    with ExitStack() as stack:
        files_16S = [stack.enter_context(gzip.open(f, 'rt')) for f in a.file_16S]
        files_28S = [stack.enter_context(gzip.open(f, 'rt')) for f in a.file_28S]
        edgefiles = [stack.enter_context(gzip.open(f, 'rt')) for f in a.file_16S + a.file_28S]
        nodeprov = RDPNodeProvider(files_16S, files_28S)
        edgeprov = RDPEdgeProvider(edgefiles)

        load_graph_delta(_LOAD_NAMESPACE, nodeprov, edgeprov, attdb,
                         a.load_timestamp, a.release_timestamp, a.load_version)


if __name__ == '__main__':
    main()
