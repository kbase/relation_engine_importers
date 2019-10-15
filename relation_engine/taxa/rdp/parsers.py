"""
Common code for dealing with RDP taxonomy files.
"""

# TODO TEST
# TODO DOCS better documentation.

import re

_16S = '16S'
_28S = '28S'
_INCERTAE_SEDIS = 'incertae_sedis'

_RE_INCERTAE_SEDIS = re.compile('[_ ][Ii]ncertae[_ ][Ss]edis')

class RDPNodeProvider:
    """
    RDPNodeProvider is an iterable that returns a new RDP taxonomy node as a dict with each
    iteration.
    """

    def __init__(self, rdp_taxonomy_16Sfile_handles, rdp_taxonomy_28Sfile_handles):
        """
        Create the node provider.

        rdp_taxonomy_16Sfile_handles - a list of open handles for the RDP taxonomy 16S files to
            process.
        rdp_taxonomy_28Sfile_handles - a list of open handles for the RDP taxonomy 28S files to
            process.
        """
        self._fh_16S = rdp_taxonomy_16Sfile_handles
        self._fh_28S = rdp_taxonomy_28Sfile_handles

    def __iter__(self):
        seen_taxa = set()  # not including leaves
        for fh in self._fh_16S:
            yield from self._processfile(_16S, fh, seen_taxa)
        for fh in self._fh_28S:
            yield from self._processfile(_28S, fh, seen_taxa)
        
    def _processfile(self, molecule, fh, seen_taxa):
        for line in fh:
            if not line.startswith('>'):
                continue
            names, lineage = line.split('\t')
            locus, definition = names.split(' ', 1)
            lineage, unclassified = _get_lineage(lineage)
            if not lineage:  # it's an outgroup
                continue
            for l in lineage:
                l_id = _taxon_to_id(l)
                if l_id not in seen_taxa:
                    yield {
                        'id': l_id.replace('/', '_'),
                        'rank': l['rank'],
                        'name': l['name'],
                        'unclassified': False,
                        'molecule': None,
                        _INCERTAE_SEDIS: l[_INCERTAE_SEDIS]
                    }
                seen_taxa.add(l_id)
            yield {
                'id': locus[1:].strip(),  # remove '>'
                'rank': 'sequence_example',
                'name': definition.strip(),
                'unclassified': unclassified,
                'molecule': molecule,
                _INCERTAE_SEDIS: None
            }

class RDPEdgeProvider:
    """
    RDPNodeProvider is an iterable that returns a new RDP taxonomy edge as a dict with each
    iteration.
    """

    def __init__(self, rdp_taxonomy_file_handles):
        """
        Create the edge provider.

        rdp_taxonomy_file_handles - a list of open handles for the RDP taxonomy files to process.
        """
        self._fh = rdp_taxonomy_file_handles

    def __iter__(self):
        seen_taxa = set()  # not including leaves
        for fh in self._fh:
            for line in fh:
                if not line.startswith('>'):
                    continue
                names, lineage = line.split('\t')
                locus, _ = names.split(' ', 1)
                locus = locus[1:].strip()  # remove '>'
                lineage, _ = _get_lineage(lineage)
                if not lineage:  # it's an outgroup
                    continue
                for i in range(len(lineage) - 1):
                    parent_id = _taxon_to_id(lineage[i]).replace('/', '_')
                    child_id = _taxon_to_id(lineage[i + 1]).replace('/', '_')
                    if child_id not in seen_taxa:
                        yield {
                            'id': child_id,  # one edge per child
                            'from': child_id,
                            'to': parent_id
                        }
                        seen_taxa.add(child_id)
                parent_id = _taxon_to_id(lineage[-1]).replace('/', '_')
                yield {
                    'id': locus,  # one edge per child
                    'from': locus,
                    'to': parent_id
                }

# returns None in the first argument if the lineage indicates an outgroup.
# second argument indicates if the sequence is unclassfied below the provided lineage
def _get_lineage(linstr):
    lin = linstr.replace('Lineage=', '')
    l = lin.split(';')
    if not l[-1].strip():
        l = l[0:-1]
    unclassified = False
    if len(l) % 2 != 0:
        if l[-1].startswith('unclassified_'):
            unclassified = True
        elif l[-1].endswith('Outgroup'):
            return None, False
        else:
            raise ValueError('Unprocessable lineage; ' + linstr)
        l = l[0:-1]
    ret = []
    for i in range(0, len(l) - 1, 2):
        name, incertae_sedis = _incertae_sedis(l[i])
        rank = l[i + 1].strip().strip('"')
        ret.append({
            'rank': rank,
            'name': name.strip('"'),
            _INCERTAE_SEDIS: incertae_sedis})
    return ret, unclassified

def _taxon_to_id(taxon):
    is_ = ':is' if taxon[_INCERTAE_SEDIS] else ''
    return f"{taxon['rank']}:{taxon['name'].replace(' ', '_')}{is_}"


def _incertae_sedis(name):
    """
    Determine if a name denotes an incertae sedis taxon placement, remove the incertae sedis text,
    and return the cleaned name (1st arg) and a boolean (2nd) that denotes whether the name
    was cleaned or not.

    This method depends heavily on the idiosyncratic way in which RDP denotes that a taxonomic
    placement is uncertain.

    For the 11.5 release, in no case was there taxa of the same rank where both the standard
    name and the incertae sedis name existed concurrently.
    """

    newname = _RE_INCERTAE_SEDIS.sub('', name.strip())
    return newname, name != newname
