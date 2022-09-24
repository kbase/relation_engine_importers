'''
PROTOTYPE

Loads a record into an ArangoDB collection for each entry in a GTDB taxomony file.

The collection must have an index for every taxonomy rank.
'''

from arango import ArangoClient
from pathlib import Path
from relation_engine.taxa.config import DeltaLoaderConfig  # TODO PROTO make own config system
# TODO PROTO move this to a shared module
from relation_engine.taxa.gtdb.parsers import _get_lineage

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
COLLECTION = 'coll_taxonomy_frequency'


def main():
    client = ArangoClient(hosts=HOST)
    with open(Path(CONFIG_FILE).expanduser(), 'rb') as c:
        cfg = DeltaLoaderConfig(c, ["bac_input_file"])  # hack for this prototype
        db = client.db(DATABASE, cfg.username, cfg.password, verify=True)
    col = db.collection(COLLECTION)
    count = 0
    for file_ in LOAD_FILES:
        with open(Path(file_).expanduser()) as inp:
        # TODO PROTO batch input to speep things up or just output to jsonl and arangoimport
            for line in inp:
                if count % 10000 == 0:
                    print("loaded", count)
                accession, lineage = line.strip().split("\t")
                lineage = _get_lineage(lineage)
                doc = {
                    "_key": f"{accession}_{LOAD_VERSION}",
                    "id": accession,
                    "load_version": LOAD_VERSION,
                    "lineage": {lin["abbrev"]: lin["name"] for lin in lineage}
                }
                col.insert(document=doc, overwrite=True, silent=True)
                count += 1

if __name__ == "__main__":
    main()