'''
PROTOTYPE

Loads a record into an ArangoDB collection for each entry in a GTDB taxomony file.

The collection must have an index for every taxonomy rank.
'''

import hashlib

from arango import ArangoClient
from collections import defaultdict
from pathlib import Path
from relation_engine.taxa.config import DeltaLoaderConfig  # TODO PROTO make own config system
# TODO PROTO move this to a shared module
from relation_engine.taxa.gtdb.parsers import _get_lineage, _TAXA_TYPES

# TODO PROTO config file for these values
LOAD_VERSION = 207
# just for arango creds
CONFIG_FILE = '~/SCIENCE/taxonomy/gtdb/load_config.toml'
LOAD_FILES = [
    '~/SCIENCE/taxonomy/gtdb/bac120_taxonomy_r207.tsv',
    '~/SCIENCE/taxonomy/gtdb/ar53_taxonomy_r207.tsv'
]
HOST = 'http://localhost:48000'
DATABASE = 'gavin_test'
ARANGO_COLLECTION = 'coll_taxonomy_frequency2'
KBASE_COLLECTION = "gtdb"


def _parse_files():
    line_count = 0
    nodes = defaultdict(lambda: defaultdict(int))
    for file_ in LOAD_FILES:
        with open(Path(file_).expanduser()) as inp:
            for line in inp:
                if line_count % 10000 == 0:
                    print("parsed", line_count)
                lineage = line.strip().split("\t")[1]
                lineage = _get_lineage(lineage)
                for lin in lineage:
                    nodes[_TAXA_TYPES[lin['abbrev']]][lin['name']] += 1
                line_count += 1
    return nodes

def main():
    nodes = _parse_files()
    node_count = sum([len(v) for v in nodes.values()])
    client = ArangoClient(hosts=HOST)
    with open(Path(CONFIG_FILE).expanduser(), 'rb') as c:
        cfg = DeltaLoaderConfig(c, ["bac_input_file"])  # hack for this prototype
        db = client.db(DATABASE, cfg.username, cfg.password, verify=True)
    col = db.collection(ARANGO_COLLECTION)
    doc_count = 0
    for rank in nodes:
        # TODO PROTO batch input to speep things up or just output to jsonl and arangoimport
        for name in nodes[rank]:
            if doc_count % 10000 == 0:
                print(f"loaded {doc_count} / {node_count}")
            doc = {
                "_key": hashlib.md5(
                    f"{KBASE_COLLECTION}_{LOAD_VERSION}_{rank}_{name}".encode('utf-8')
                    ).hexdigest(),
                "collection": KBASE_COLLECTION,
                "load_version": LOAD_VERSION,
                "rank": rank,
                "name": name,
                "count": nodes[rank][name]
            }
            col.insert(document=doc, overwrite=True, silent=True)
            doc_count += 1

if __name__ == "__main__":
    main()