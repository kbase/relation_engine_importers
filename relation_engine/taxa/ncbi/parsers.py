"""
Common code for dealing with NCBI taxonomy files.
"""

# Since this is KBase internal code we can be a bit less compassionate re good
# error messages, e.g. throwing KeyErrors or TypeErrors vs a more descriptive message.
# Similarly, since the input is NCBI taxa dumps we probably don't need to worry much about
# malformed input.
# As a result we get slightly less code to maintain and a completely trivial performance boost.
# And there was much rejoicing.


import re
from collections import defaultdict

from relation_engine.taxa.common_fields import (
    FROM,
    TO,
    ID,
    SCI_NAME,
    RANK,
    SPECIES_OR_BELOW,
)

from relation_engine.taxa.ncbi.ranks import (
    RANKS_ALL,
    RANKS_SPECIES_AND_BELOW,
    RANKS_NON_HIERARCHICAL,
)

_SEP = r'\s\|\s?'
_SCI_NAME = 'scientific name'


class NCBINodeProvider:
    """
    NCBINodeProvider is an iterable that returns a new NCBI taxonomy node as a dict with each
    iteration.
    It requires access to the names.dmp and nodes.dmp files from a taxonomy dump.
    """

    def __init__(self, names_filehandle, nodes_filehandle):
        """
        Create the provider.
        names_filehandle - the opened names.dmp file.
        nodes_filehandle - the opened nodes.dmp file. This file handle must be seek-able.
        """
        self._names = self._load_names(names_filehandle)
        self._node_fh = nodes_filehandle
        # contains strings, not numbers
        # species and subspecies
        self._species_tax_ids = set()
        # anything that has no rank and links to species, subspecies, or strains
        self._strain_tax_ids = set()
        self._get_species_and_strain_ids()

    def _load_names(self, name_file):
        # Could make this use less memory by parsing one nodes worth of entries at a time, since
        # both the names and nodes files are sorted by taxid. YAGNI for now
        name_table = defaultdict(lambda: defaultdict(list))
        for line in name_file:
            # this is pretty fragile, but we don't expect the NCBI dump files to have errors
            # and adding a lot of checking would be a lot of code to maintain for little purpose
            tax_id, name, _, category = re.split(_SEP, line)[0:4]
            name_table[tax_id.strip()][category.strip()].append(name.strip())

        return {k: dict(name_table[k]) for k in name_table.keys()}

    def _get_species_and_strain_ids(self):
        # Almost certainly faster to just load the tree into memory in one pass and recurse.
        # Originally written this way to avoid memory usage, but > 80% of the node
        # IDs are going to be stored in memory either way.
        # Alternately make a sqlite DB or something
        # Given the use case is a batch load ~ 1 / month, YAGNI
        not_converged = True
        count = 1
        while not_converged:
            print(f'strain determination round {count}')
            count += 1
            not_converged = False
            for line in self._node_fh:
                # also fragile
                record = re.split(_SEP, line)
                id_, parent, rank = [record[i].strip() for i in [0, 1, 2]]
                if rank not in RANKS_ALL:
                    raise ValueError(f"Node {id_} has an unexpected rank of {rank}")
                if rank in RANKS_SPECIES_AND_BELOW:
                    self._species_tax_ids.add(id_)  # after the first round this is a no-op
                elif (rank in RANKS_NON_HIERARCHICAL
                        and id_ not in self._strain_tax_ids
                        and (parent in self._species_tax_ids or parent in self._strain_tax_ids)):
                    not_converged = True
                    self._strain_tax_ids.add(id_)
            self._node_fh.seek(0)

    def __iter__(self):
        for line in self._node_fh:
            record = re.split(_SEP, line)
            # should really make the ints constants but meh
            id_, rank, gencode = [record[i].strip() for i in [0, 2, 6]]

            aliases = []
            # May need to move names into separate nodes for canonical search purposes
            for cat in list(self._names[id_].keys()):
                if cat != _SCI_NAME:
                    for nam in self._names[id_][cat]:
                        aliases.append({'category':  cat, 'name': nam})

            # vertex
            sci_names = self._names[id_][_SCI_NAME]
            if len(sci_names) != 1:
                raise ValueError('Node {} has {} scientific names'.format(id_, len(sci_names)))
            node = {
                ID:                         id_,
                SCI_NAME:            sci_names[0],
                RANK:                       rank,
                # strain is deprecated, confusing, and collides with the new NCBI strain rank
                # but is kept for backwards compatibilty reasons
                'strain':                     id_ in self._strain_tax_ids,
                SPECIES_OR_BELOW:             (id_ in self._strain_tax_ids
                                               or id_ in self._species_tax_ids),
                'aliases':                    aliases,
                'ncbi_taxon_id':              int(id_),
                'gencode':                    int(gencode),
            }

            yield node


class NCBIEdgeProvider:
    """
    NCBIEdgeProvider is an iterable that returns a new NCBI taxonomy edge as a dict where the
    from key is the child ID and the to key the parent ID with each iteration.
    It requires access to the nodes.dmp files from a taxonomy dump.
    """

    def __init__(self, nodes_filehandle):
        """
        Create the provider.
        nodes_filehandle - the opened nodes.dmp file.
        """
        self._node_fh = nodes_filehandle

    def __iter__(self):
        for line in self._node_fh:
            # fragile
            record = re.split(_SEP, line)
            # should really make the ints constants but meh
            id_, parent = [record[i].strip() for i in [0, 1]]

            if id_ == parent:
                continue  # no self edges

            edge = {
                ID: id_,  # since there's 1 edge / child the child id uniquely IDs the edge
                FROM: id_,
                TO: parent
            }
            yield edge


class NCBIMergeProvider:
    """
    NCBIMergeProvider is an iterable that returns merged node information as a dict where the from
    key is the merged node ID and the to key the merge target node ID.
    """

    def __init__(self, merges_filehandle):
        """
        Create the provider.
        merges_filehandle - the open merged.dmp file.
        """
        self._merge_fh = merges_filehandle

    def __iter__(self):
        for line in self._merge_fh:
            # fragile
            record = re.split(_SEP, line)
            merged = record[0].strip()
            edge = {
                ID: merged,  # since you can't merge into multiple nodes, the id is a unique id
                FROM: merged,
                TO: record[1].strip()
            }
            yield edge
