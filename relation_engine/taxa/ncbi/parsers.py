"""
Common code for dealing with NCBI taxonomy files.
"""

# TODO TEST

import re
from collections import defaultdict

_SEP = r'\s\|\s?'
_SCI_NAME = 'scientific name'
_RANK_SPECIES = 'species'
_RANK_NO_RANK = 'no rank'
_RANK_SUBSPECIES = 'subspecies'
# Based on the August 2019 NCBI release, species groups and subgroups do not link to strains.
# The child nodes have names like "ananassae species complex" or "mayaguana subcluster" or
# "unclassified Bisgaard taxa
_SPECIES_RANKS = set([_RANK_SPECIES, _RANK_SUBSPECIES])


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
            tax_id, name, _, category = re.split(_SEP, line)[0:4]
            name_table[tax_id.strip()][category.strip()].append(name.strip())

        return {k: dict(name_table[k]) for k in name_table.keys()}

    def _get_species_and_strain_ids(self):
        not_converged = True
        count = 1
        while not_converged:
            print(f'strain determination round {count}')
            count += 1
            not_converged = False
            for line in self._node_fh:
                record = re.split(_SEP, line)
                id_, parent, rank = [record[i].strip() for i in [0, 1, 2]]
                if rank in _SPECIES_RANKS:
                    self._species_tax_ids.add(id_)  # after the first round this is a no-op
                elif (rank == _RANK_NO_RANK
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
                'id':                         id_,
                'scientific_name':            sci_names[0],
                'rank':                       rank,
                'strain':                     id_ in self._strain_tax_ids,
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
            record = re.split(_SEP, line)
            # should really make the ints constants but meh
            id_, parent = [record[i].strip() for i in [0, 1]]

            if id_ == parent:
                continue  # no self edges

            edge = {
                'id': id_,  # since there's 1 edge / child the child id uniquely IDs the edge
                'from': id_,
                'to': parent
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
            record = re.split(_SEP, line)
            merged = record[0].strip()
            edge = {
                'id': merged,  # since you can't merge into multiple nodes, the id is a unique id
                'from': merged,
                'to': record[1].strip()
            }
            yield edge
