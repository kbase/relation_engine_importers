from parsers import TaxNode, SILVANodeProvider, SILVAEdgeProvider
from util.dprint import dprint
import json
import os
import unittest


cwd = os.path.dirname(os.path.abspath(__file__))
sample_flnm = 'tax_slv_ssu_138_sample.txt'
full_flnm = 'tax_slv_ssu_138.txt'


class SILVAProviderTest(unittest.TestCase):
    '''
    For testing SILVANodeProvider, SILVAEdgeProvider, and their auxiliary TaxNode

    Steps are
    1. Parse taxonomy file
    2. Iterable for node dicts
    3. Iterable for edge dicts
    '''

    def _run(self, flpth):
        '''
        Parse taxonomy file and get node/edge dicts
        '''

        TaxNode.parse_taxfile(flpth)

        node_prov = SILVANodeProvider(TaxNode)
        edge_prov = SILVAEdgeProvider(TaxNode)

        nodes = []
        edges = []

        for node in iter(node_prov):
            nodes.append(node)

        for edge in iter(edge_prov):
            edges.append(edge)

        return nodes, edges

    def _check(self, nodes, edges, nodes_flpth, edges_flpth, mode='test'):
        '''
        Check resultant node/edge dicts

        Inputs:
        * nodes - list of dicts from `SILVANodeProvider`
        * edges - list of dicts from `SILVAEdgeProvider`
        * nodes_flpth - reference nodes written
        * edges_flpth - reference edges written
        * mode - {'write', 'test'}
        '''

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


    def test_sample(self, mode='test'):
        '''
        Test against small sample taxonomy file
        '''

        nodes, edges = self._run(os.path.join(cwd, 'data/sample', sample_flnm))

        nodes_flpth = os.path.join(cwd, 'data/sample', 'nodes.json')
        edges_flpth = os.path.join(cwd, 'data/sample', 'edges.json')

        self._check(nodes, edges, nodes_flpth, edges_flpth, mode=mode)


    def test_SILVA_full(self, mode='test'):
        '''
        Test against full SILVA taxonomy file
        '''
        nodes, edges = self._run(os.path.join(cwd, 'data/full', full_flnm))

        nodes_flpth = os.path.join(cwd, 'data/full', 'nodes.json')
        edges_flpth = os.path.join(cwd, 'data/full', 'edges.json')

        self._check(nodes, edges, nodes_flpth, edges_flpth, mode=mode)

        # spot checks

        tax_trav = TaxpathTraverser(nodes, edges)

        taxpath = 'Bacteria;Desulfobacterota;Thermodesulfobacteria;Thermodesulfobacteriales;Thermodesulfobacteriaceae;Geothermobacterium;'
        taxid = 45081
        rank = 'genus'
        release = 138

        tax_trav.traverse_check(taxpath, taxid, rank, release)

        taxpath = 'Bacteria;Proteobacteria;Gammaproteobacteria;Gammaproteobacteria Incertae Sedis;Unknown Family;Endothiovibrio;'
        taxid = 26666
        rank = 'genus'
        release = 132

        tax_trav.traverse_check(taxpath, taxid, rank, release)


    def test_url_input(self, mode='test'):
        '''
        Test inputting the SILVA taxonomy file download URL
        '''
        nodes, edges = self._run(
            'https://www.arb-silva.de/fileadmin/silva_databases/release_138/Exports/taxonomy/tax_slv_ssu_138.txt.gz',
            compression='gzip'
        )
        nodes_flpth = os.path.join(cwd, 'data/full', 'nodes.json')
        edges_flpth = os.path.join(cwd, 'data/full', 'edges.json')

        self._check(nodes, edges, nodes_flpth, edges_flpth, mode=mode)

        # spot checks

        tax_trav = TaxpathTraverser(nodes, edges)

        taxpath = 'Bacteria;Desulfobacterota;Thermodesulfobacteria;Thermodesulfobacteriales;Thermodesulfobacteriaceae;Geothermobacterium;'
        taxid = 45081
        rank = 'genus'
        release = 138

        tax_trav.traverse_check(taxpath, taxid, rank, release)

        taxpath = 'Bacteria;Proteobacteria;Gammaproteobacteria;Gammaproteobacteria Incertae Sedis;Unknown Family;Endothiovibrio;'
        taxid = 26666
        rank = 'genus'
        release = 132

        tax_trav.traverse_check(taxpath, taxid, rank, release)


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

    def tax_to_node(self, name, taxid, rank, release):
        '''
        Inputs from taxonomy file
        Find corresponding `node` from SILVA node provider
        '''
        for node in self.nodes:
            if (node['id'] == taxid and
                node['name'] == name and
                node['rank'] == rank and
                node['release'] == release):
                return node
        raise Exception()

    def node_to_edge(self, node: dict):
        '''
        Get outgoing edge from node

        `node` is from SILVANodeProvider
        '''
        taxid = node['id']
        for edge in self.edges:
            if taxid == edge['from']:
                return edge
        raise Exception()

    def edge_to_node(self, edge: dict):
        '''
        Get child node from edge

        `edge` is from SILVAEdgeProvider
        '''
        taxid = edge['to']
        for node in self.nodes:
            if taxid == node['id']:
                return node
        raise Exception()
    
    def traverse_check(self, taxpath, taxid, rank, release):

        tax_l = taxpath.split(';')[:-1] # semicolon-terminated

        node = self.tax_to_node(tax_l[-1], taxid, rank, release) # locate `node` corresponding to lowest taxon

        for tax in tax_l[:-1][::-1]: # go backwards from second-to-last

            edge = self.node_to_edge(node)
            node = self.edge_to_node(edge)

            self.assertTrue(node['name'] == tax, f"`node['name']` is {node['name']}, `tax` is {tax}")

        print('Done traversing %s' % taxpath)

    @staticmethod
    def assertTrue(self, expr, msg=''):
        if not expr:
            raise AssertionError(msg)


if __name__ == '__main__':
    unittest.main()
