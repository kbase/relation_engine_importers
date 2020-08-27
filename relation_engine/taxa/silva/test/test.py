from relation_engine.taxa.silva.parsers import TaxNode, SeqNode, SILVANodeProvider, SILVAEdgeProvider
from relation_engine.taxa.silva.util.dprint import dprint
import json
import os
import sys
import unittest


cwd = os.path.dirname(os.path.abspath(__file__))


class SILVAProviderTest(unittest.TestCase):
    '''
    For testing SILVANodeProvider, SILVAEdgeProvider, and their auxiliary TaxNode

    Steps are
    1. Parse taxonomy file
    2. Iterable for node dicts
    3. Iterable for edge dicts
    '''

    def _run(self, input_dir):
        '''
        Parse taxonomy file and get node/edge dicts
        '''

        TaxNode.parse_taxfile(input_dir)
        SeqNode.parse_fastas(input_dir)

        node_prov = SILVANodeProvider()
        edge_prov = SILVAEdgeProvider()

        nodes = []
        edges = []

        for node in iter(node_prov):
            nodes.append(node)

        for edge in iter(edge_prov):
            edges.append(edge)

        return nodes, edges

    def _check_superficial(self, nodes, edges, nodes_flpth, edges_flpth, mode='test'):
        '''
        Check resultant node/edge dicts

        Inputs:
        * nodes - list of dicts from `SILVANodeProvider`
        * edges - list of dicts from `SILVAEdgeProvider`
        * nodes_flpth - reference nodes written
        * edges_flpth - reference edges written
        * mode - {'write', 'test'}
        '''

        dprint(
            'nodes',
            'len(nodes)',
            'edges',
            'len(edges)',
            run=locals(),
            max_lines=30
        )

        # check uniqueness of `nodes` and `edges`

        nodes_str_l = [str(n) for n in nodes] # convert to list of strings
        edges_str_l = [str(e) for e in edges] # since dicts are unhashable and want to use `set`

        self.assertTrue(len(set(nodes_str_l)) == len(nodes_str_l))
        self.assertTrue(len(set(edges_str_l)) == len(edges_str_l))

        # write reference (do visual check)
        if mode == 'write':
            with open(nodes_flpth, 'w') as fh:
                json.dump(nodes, fh, indent=3)

            with open(edges_flpth, 'w') as fh:
                json.dump(edges, fh, indent=3)

        # test against reference
        elif mode == 'test':
            with open(nodes_flpth) as fh:
                nodes_ref = json.load(fh)

            with open(edges_flpth) as fh:
                edges_ref = json.load(fh)

            self.assertTrue(nodes == nodes_ref)
            self.assertTrue(edges == edges_ref)

        else:
            raise Exception()


    @unittest.skip('Temp')
    def test_sample(self, mode='write'):
        '''
        Test against small sample taxonomy file
        '''

        nodes, edges = self._run(os.path.join(cwd, 'data/sample'))

        nodes_flpth = os.path.join(cwd, 'data/sample', 'nodes.json')
        edges_flpth = os.path.join(cwd, 'data/sample', 'edges.json')

        self._check_superficial(nodes, edges, nodes_flpth, edges_flpth, mode=mode)


    def test_SILVA_full(self, mode='write'):
        '''
        Test against full SILVA taxonomy file
        '''
        nodes, edges = self._run(os.path.join(cwd, 'data/full'))

        nodes_flpth = os.path.join(cwd, 'data/full', 'nodes.json')
        edges_flpth = os.path.join(cwd, 'data/full', 'edges.json')

        self._check_superficial(nodes, edges, nodes_flpth, edges_flpth, mode=mode)

        # spot check taxon nodes

        tax_trav = TaxpathTraverser(nodes, edges)

        taxpath = 'Bacteria;Desulfobacterota;Thermodesulfobacteria;Thermodesulfobacteriales;Thermodesulfobacteriaceae;Geothermobacterium;'
        taxid = 45081
        rank = 'genus'
        release = 138

        tax_trav.traverse_check_taxon(taxpath, taxid, rank, release)

        taxpath = 'Bacteria;Proteobacteria;Gammaproteobacteria;Gammaproteobacteria Incertae Sedis;Unknown Family;Endothiovibrio;'
        taxid = 26666
        rank = 'genus'
        release = 132

        tax_trav.traverse_check_taxon(taxpath, taxid, rank, release)

        # spot check sequence nodes

        id = 'CP020647.3123215.3124757'
        name = 'Bordetella holmesii'
        rank = 'sequence'
        sequence = 'AGAGAUUAAACUGAAGAGUUUGAUCCUGGCUCAGAUUGAACGCUGGCGGGAUGCUUUACACAUGCAAGUCGGACGGCAGCACGGGGCUUCGGCCUGGUGGCGAGUGGCGAACGGGUGAGUAAUGUAUCGGAACGUGCCCGGUAGCGGGGGAUAACUACGCGAAAGCGUGGCUAAUACCGCAUACGCCCUACGGGGGAAAGCGGGGGACCUUCGGGCCUCGCACUAUUGGAGCGGCCGAUAUCGGAUUAGCUAGUUGGUGGGGUAACGGCCUACCAAGGCGACGAUCCGUAGCUGGUUUGAGAGGACGACCAGUCACACUGGGACUGAGACACGGCCCAGACUCCUACGGGAGGCAGCAGUGGGGAAUUUUGGACAAUGGGGGCAACCCUGAUCCAGCCAUCCCGCGUGUGCGAUGAAGGCCUUCGGGUUGUAAAGCACUUUUGGCAGGAAAGAAACGGCACGGGCUAAUAUCCUGUGCAACUGACGGUACCUGCAGAAUAAGCACCGGCUAACUACGUGCCAGCAGCCGCGGUAAUACGUAGGGUGCAAGCGUUAAUCGGAAUUACUGGGCGUAAAGCGUGCGCAGGCGGUUCGGAAAGAAAGAUGUGAAAUCCCAGGGCUUAACCUUGGAACUGCAUUUUUAACUACCGAGCUAGAGUGUGUCAGAGGGAGGUGGAAUUCCGCGUGUAGCAGUGAAAUGCGUAGAUAUGCGGAGGAACACCGAUGGCGAAGGCAGCCUCCUGGGAUAACACUGACGCUCAUGCACGAAAGUGUGGGGAGCAAACAGGAUUAGAUACCCUGGUAGUCCACGCCCUAAACGAUGUCAACUAGCUGUUGGGGCCUUCGGGCCUUGGUAGCGCAGCUAACGCGUGAAGUUGACCGCCUGGGGAGUACGGUCGCAAGAUUAAAACUCAAAGGAAUUGACGGGGACCCGCACAAGCGGUGGAUGAUGUGGAUUAAUUCGAUGCAACGCGAAAAACCUUACCUACCCUUGACAUGUCUGGAAUCCCGAAGAGAUUUGGGAGUGCUCGCAAGAGAACCGGAACACAGGUGCUGCAUGGCUGUCGUCAGCUCGUGUCGUGAGAUGUUGGGUUAAGUCCCGCAACGAGCGCAACCCUUGUCAUUAGUUGCUACGAAAGGGCACUCUAAUGAGACUGCCGGUGACAAACCGGAGGAAGGUGGGGAUGACGUCAAGUCCUCAUGGCCCUUAUGGGUAGGGCUUCACACGUCAUACAAUGGUCGGGACAGAGGGUUGCCAACCCGCGAGGGGGAGCCAAUCCCAGAAACCCGGUCGUAGUCCGGAUCGCAGUCUGCAACUCGACUGCGUGAAGUCGGAAUCGCUAGUAAUCGCGGAUCAGCAUGUCGCGGUGAAUACGUUCCCGGGUCUUGUACACACCGCCCGUCACACCAUGGGAGUGGGUUUUACCAGAAGUAGUUAGCCUAACCGCAAGGGGGGCGAUUACCACGGUAGGAUUCAUGACUGGGGUGAAGUCGUAACAAGGUAGCCGUAUCGGAAGGUGCGGCUGGAUCACCUCCUUUAAGA'
        datasets = ['ref', 'nr99']
        taxpath = 'Bacteria;Proteobacteria;Gammaproteobacteria;Burkholderiales;Alcaligenaceae;Bordetella;'

        tax_trav.traverse_check_sequence(id, name, rank, sequence, datasets, taxpath)


        id = 'HM112903.1.1368'
        name = 'uncultured beta proteobacterium'
        rank = 'sequence'
        sequence = 'GAUUGAACGCUGGCGGCAUGCCUUACACAUGCAAGUCGAACGGCAGCACGGGUGCUUGCACCUGGUGGCGAGUGGCGAACGGGUGAGUAAUACAUCGGAACAUGUCCUGUAGUGGGGGAUAGCCCGGCGAAAGCCGGAUUAAUACCGCAUACGAUCUACGGAUGAAAGCGGGGGACCUUCGGGCCUCGCGCUAUAGGGUUGGCCGAUGGCUGAUUAGCUAGUUGGUGGGGUAAAGGCCUACCAAGGCGACGAUCAGUAGCUGGUCUGAGAGGACGACCAGCCACACUGGGACUGAGACACGGCCCAGACUCCUACGGGAGGCAGCAGUGGGGAAUUUUGGACAAUGGGCGAAAGCCUGAUCCAGCAAUGCCGCGUGUGUGAAGAAGGCCUUCGGGUUGUAAAGCACUUUUGUCCGGAAAGAAAUCCUUGGCUCUAAUACAGUCGGGGGAUGACGGUACCGGAAGAAUAAGCACCGGCUAACUACGUGCCAGCAGCCGCGGUAAUACGUAGGGUGCGAGCGUUAAUCGGAAUUACUGGGCGUAAAGCGUGCGCAGGCGGUUUGCUAAGACCGAUGUGAAAUCCCCGGGCUCAACCUGGGAACUGCAUUGGUGACUGGCAGGCUAGAGUAUGGCAGAGGGGGGUAGAAUUCCACGUGUAGCAGUGAAAUGCGUAGAGAUGUGGAGGAAUACCGAUGGCGAAGGCAGCCCCCUGGGCCAAUACUGACGCUCAUGCACGAAAGCGUGGGGAGCAAACAGGAUUAGAUACCCUGGUAGUCCACGCCCUAAACGAUGUCAACUAGUUGUUGGGGAUUCAUUUCCUUAGUAACGUAGCUAACGCGUGAAGUUGACCGCCUGGGGAGUACGGUCGCAAGAUUAAAACUCAAGGGAAUUGACGGGGACCCGCACAAGCGGUGGAUGAUGUGGAUUAAUUCGAUGCAACGCGAAAAACCUUACCUACCCUUGACAUGGUCGGAAUCCUGCUGAGAGGCGGGAGUGCUCGAAAGAGAACCGGCGCACAGGUGCUGCAUGGCUGUCGUCAGCUCGUGUCGUGAGAUGUUGGGUUAAGUCCCGCAACGAGCGCAACCCUUGUCCUUAGUUGCUACGCAAGAGCACUCUAAGGAGACUGCCGGUGACAAACCGGAGGAAGGUGGGGAUGACGUCAAGUCCUCAUGGCCCUUAUGGGUAGGGCUUCACACGUCAUACAAUGGUCGGAACAGAGGGUUGCCAACCCGCGAGGGGGAGCUAAUCCCAGAAAACCGAUCGUAGUCCGGAUUGCACUCUGCAACUCGAGUGCAUGAAGCUGGAAUCGCUAGUAAUCGCGGAUCAGCAUGCCGCGGUGAAUACGUUCCCGGGUCUUGUACACACCGCC'
        datasets = ['ref']
        taxpath = 'Bacteria;Proteobacteria;Gammaproteobacteria;Burkholderiales;Burkholderiaceae;Burkholderia-Caballeronia-Paraburkholderia;'

        tax_trav.traverse_check_sequence(id, name, rank, sequence, datasets, taxpath)

    def shortDescription(self):
        '''Override unittest using test*() docstrings in lieu of test*() method name in output summary'''
        return None


class TaxpathTraverser:
    '''
    Auxiliary class for SILVAProviderTest
    Help verify that paths from taxonomy file are represented by `nodes` and `edges` lists of dicts
    '''

    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def _info_to_node(self, id: str, name: str, rank: str, release=None, sequence=None, datasets=None):
        '''
        Inputs from taxonomy file
        Find corresponding `node` from SILVA node provider
        '''
        if id.isnumeric():
            print('numeric')
            for node in self.nodes:
                if (node['id'] == id and
                    node['name'] == name and
                    node['rank'] == rank and
                    node['release'] == release):
                    return node
        else:
            for node in self.nodes:
                if (node['id'] == id and
                    node['name'] == name and
                    node['rank'] == rank and
                    node['sequence'] == sequence): # TODO add datasets when do all
                    return node

        raise Exception(
            f"id={id}, name={name}, rank={rank}, release={release}, sequence={sequence}, datasets={datasets}")

    def _node_to_edge(self, node: dict):
        '''
        Get outgoing edge from node

        `node` is from SILVANodeProvider
        '''
        taxid = node['id']
        for edge in self.edges:
            if taxid == edge['from']:
                return edge
        raise Exception()

    def _edge_to_node(self, edge: dict):
        '''
        Get child node from edge

        `edge` is from SILVAEdgeProvider
        '''
        id = edge['to']
        for node in self.nodes:
            if id == node['id']:
                return node
        raise Exception(str(edge))

    def traverse_check_sequence(self, id, name, rank, sequence, datasets, taxpath):
        '''
        '''
        tax_l = taxpath.split(';')[:-1]

        node = self._info_to_node(id, name, rank, sequence=sequence, datasets=datasets)

        for tax in tax_l[::-1]: # go backwards

            edge = self._node_to_edge(node)
            node = self._edge_to_node(edge)

            self.assertTrue(node['name'] == tax, f"`node['name']` is {node['name']}, `tax` is {tax}")

        print('Done traversing %s' % taxpath)
    
    def traverse_check_taxon(self, taxpath, taxid, rank, release):
        '''
        Given info of taxon node,
        traverse up its path through provided nodes/edges
        making sure those match the taxonomy in the taxon node
        '''

        tax_l = taxpath.split(';')[:-1] # semicolon-terminated

        node = self._info_to_node(str(taxid), tax_l[-1], rank, release=release) # locate `node` corresponding to lowest taxon

        for tax in tax_l[:-1][::-1]: # go backwards from second-to-last

            edge = self._node_to_edge(node)
            node = self._edge_to_node(edge)

            self.assertTrue(node['name'] == tax, f"`node['name']` is {node['name']}, `tax` is {tax}")

        print('Done traversing %s' % taxpath)

    @staticmethod
    def assertTrue(self, expr, msg=''):
        if not expr:
            raise AssertionError(msg)


if __name__ == '__main__':
    unittest.main()
