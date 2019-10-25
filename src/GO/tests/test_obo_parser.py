"""
Test obo_parser
"""
from GO import obo_parser
import unittest
import os
import sys
sys.path.append('../')


def get_file_dir():
    return os.path.dirname(__file__)


class TestOboParser(unittest.TestCase):
    def test_read_GO_obo_file(self):
        """
        Test reading the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'go.obo')
        with open(path, 'rt') as read_file:
            go = obo_parser.read_obo(read_file)
            self.assertEqual(len(go), 47401)
            self.assertEqual(go.nodes["GO:0000016"]["name"], "lactase activity")
            self.assertEqual(go.nodes["GO:0000018"]["relationship"], ["regulates GO:0006310"])
            self.assertEqual(go.nodes["GO:0000019"]["intersection_of"], ["GO:0008150", "regulates GO:0006312"])
            self.assertEqual(go.nodes["GO:0000022"]["namespace"], "biological_process")
            self.assertTrue('EC:3.1.13' in go.nodes["GO:0000175"]["xref"])

    def test_read_obsolete_terms(self):
        """
        Test reading obsolete terms in the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'go.obo')
        with open(path, 'rt') as read_file:
            go = obo_parser.read_obo(read_file)
            self.assertEqual(go.nodes["GO:0000020"]["is_obsolete"], "true")
            self.assertRaises(KeyError, lambda: go.nodes["GO:0000022"]["is_obsolete"])
            self.assertEqual(go.nodes["GO:0000005"]["is_obsolete"], "true")
            self.assertEqual(go.nodes["GO:0000005"]["consider"], ["GO:0042254", "GO:0044183", "GO:0051082"])
            self.assertEqual(go.nodes["GO:0000174"]["is_obsolete"], "true")
            self.assertEqual(go.nodes["GO:0000174"]["replaced_by"], ["GO:0000750"])


if __name__ == '__main__':
    # Use this if running from command line
    unittest.main()
    # Use this if running from iPython notebook
    # unittest.main(argv=['first-arg-is-ignored'], exit=False)
