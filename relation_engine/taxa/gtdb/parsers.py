"""
Common code for dealing with GTDB taxonomy files.

Parses the taxonomy file, not the metadata file.
"""

from relation_engine.taxa.common_fields import (
    FROM,
    TO,
    ID,
    SCI_NAME,
    RANK,
    SPECIES_OR_BELOW,
)

# Since this is KBase internal code we can be a bit less compassionate re good
# error messages, e.g. throwing KeyErrors or TypeErrors vs a more descriptive message.
# Similarly, since the input is GTDB taxa files we probably don't need to worry much about
# malformed input.
# As a result we get slightly less code to maintain and a completely trivial performance boost.
# And there was much rejoicing.

# TODO DOCS better documentation.

_ABBRV_SPECIES = "s"

_TAXA_TYPES = {
    "d": "domain",
    "p": "phylum",
    "c": "class",
    "o": "order",
    "f": "family",
    "g": "genus",
    _ABBRV_SPECIES: "species",
}


class GTDBNodeProvider:
    """
    GTDBNodeProvider is an iterable that returns a new GTDB taxonomy node as a dict with each
    iteration.
    """

    def __init__(self, gtdb_bacterial_taxonomy_file_handle, gtdb_archaeal_taxonomy_file_handle):
        """
        Create the node provider.

        gtdb_bacterial_taxonomy_file_handle - an open handle to the bacterial GTDB taxonomy file
            to process.
        gtdb_archaeal_taxonomy_file_handle - an open handle to the archaeal GTDB taxonomy file
            to process.
        """
        self._bac_fh = gtdb_bacterial_taxonomy_file_handle
        self._arc_fh = gtdb_archaeal_taxonomy_file_handle

    def __iter__(self):
        seen_taxa = set()  # not including leaves
        for fh in [self._bac_fh, self._arc_fh]:
            for line in fh:
                accession, lineage = line.strip().split("\t")
                lineage = _get_lineage(lineage)
                for lin in lineage:
                    l_id = _taxon_to_id(lin)
                    if l_id not in seen_taxa:
                        yield {
                            ID: l_id,
                            RANK: _TAXA_TYPES[lin["abbrev"]],
                            SCI_NAME: lin["name"],
                            SPECIES_OR_BELOW: lin["abbrev"] == _ABBRV_SPECIES
                        }
                    seen_taxa.add(l_id)
                yield {
                    ID: accession,
                    RANK: "genome",
                    SCI_NAME: lineage[-1]["name"],
                    SPECIES_OR_BELOW: True
                }


class GTDBEdgeProvider:
    """
    GTDBNodeProvider is an iterable that returns a new GTDB taxonomy edge as a dict with each
    iteration.
    """

    def __init__(self, gtdb_bacterial_taxonomy_file_handle, gtdb_archaeal_taxonomy_file_handle):
        """
        Create the edge provider.

        gtdb_bacterial_taxonomy_file_handle - an open handle to the bacterial GTDB taxonomy file
            to process.
        gtdb_archaeal_taxonomy_file_handle - an open handle to the archaeal GTDB taxonomy file
            to process.
        """
        self._bac_fh = gtdb_bacterial_taxonomy_file_handle
        self._arc_fh = gtdb_archaeal_taxonomy_file_handle

    def __iter__(self):
        seen_taxa = set()  # not including leaves
        for fh in [self._bac_fh, self._arc_fh]:
            for line in fh:
                accession, lineage = line.strip().split("\t")
                lineage = _get_lineage(lineage)
                for i in range(len(lineage) - 1):
                    parent_id = _taxon_to_id(lineage[i])
                    child_id = _taxon_to_id(lineage[i + 1])
                    if child_id not in seen_taxa:
                        yield {
                            ID: child_id,  # one edge per child
                            FROM: child_id,
                            TO: parent_id
                        }
                    seen_taxa.add(child_id)
                parent_id = _taxon_to_id(lineage[-1])
                yield {
                    ID: accession,  # one edge per child
                    FROM: accession,
                    TO: parent_id
                }


def _get_lineage(linstr):
    ln = linstr.split(";")
    ret = []
    for lin in ln:
        taxa_abbrev, taxa_name = lin.split("__")
        ret.append({"abbrev": taxa_abbrev, "name": taxa_name})
    if ret[-1]["abbrev"] != "s":
        raise ValueError(f"Lineage {linstr} does not end with species")
    return ret


def _taxon_to_id(taxon):
    return f'{taxon["abbrev"]}:{taxon["name"].replace(" ", "_")}'
