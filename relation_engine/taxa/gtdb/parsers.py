"""
Common code for dealing with GTDB taxonomy files.

Parses the taxonomy file, not the metadata file.
"""

# Since this is KBase internal code we can be a bit less compassionate re good
# error messages, e.g. throwing KeyErrors or TypeErrors vs a more descriptive message.
# Similarly, since the input is GTDB taxa files we probably don't need to worry much about
# malformed input.
# As a result we get slightly less code to maintain and a completely trivial performance boost.
# And there was much rejoicing.

# TODO DOCS better documentation.

_TAXA_TYPES = {
    'd': 'domain',
    'p': 'phylum',
    'c': 'class',
    'o': 'order',
    'f': 'family',
    'g': 'genus',
    's': 'species',
}


class GTDBNodeProvider:
    """
    GTDBNodeProvider is an iterable that returns a new GTDB taxonomy node as a dict with each
    iteration.
    """

    def __init__(self, gtdb_taxonomy_file_handle):
        """
        Create the node provider.

        gtdb_taxonomy_file_handle - an open handle to the GTDB taxonomy file to process.
        """
        self._fh = gtdb_taxonomy_file_handle

    def __iter__(self):
        seen_taxa = set()  # not including leaves
        for line in self._fh:
            accession, lineage = line.strip().split('\t')
            lineage = _get_lineage(lineage)
            for lin in lineage:
                l_id = _taxon_to_id(lin)
                if l_id not in seen_taxa:
                    yield {
                        'id': l_id,
                        'rank': _TAXA_TYPES[lin['abbrev']],
                        'name': lin['name']
                    }
                seen_taxa.add(l_id)
            yield {
                'id': accession,
                'rank': 'genome',
                'name': lineage[-1]['name']
            }


class GTDBEdgeProvider:
    """
    GTDBNodeProvider is an iterable that returns a new GTDB taxonomy edge as a dict with each
    iteration.
    """

    def __init__(self, gtdb_taxonomy_file_handle):
        """
        Create the edge provider.

        gtdb_taxonomy_file_handle - an open handle to the GTDB taxonomy file to process.
        """
        self._fh = gtdb_taxonomy_file_handle

    def __iter__(self):
        seen_taxa = set()  # not including leaves
        for line in self._fh:
            accession, lineage = line.strip().split('\t')
            lineage = _get_lineage(lineage)
            for i in range(len(lineage) - 1):
                parent_id = _taxon_to_id(lineage[i])
                child_id = _taxon_to_id(lineage[i + 1])
                if child_id not in seen_taxa:
                    yield {
                        'id': child_id,  # one edge per child
                        'from': child_id,
                        'to': parent_id
                    }
                seen_taxa.add(child_id)
            parent_id = _taxon_to_id(lineage[-1])
            yield {
                'id': accession,  # one edge per child
                'from': accession,
                'to': parent_id
            }


def _get_lineage(linstr):
    ln = linstr.split(';')
    ret = []
    for lin in ln:
        taxa_abbrev, taxa_name = lin.split('__')
        ret.append({'abbrev': taxa_abbrev, 'name': taxa_name})
    if ret[-1]['abbrev'] != 's':
        raise ValueError(f'Lineage {linstr} does not end with species')
    return ret


def _taxon_to_id(taxon):
    return f"{taxon['abbrev']}:{taxon['name'].replace(' ', '_')}"
