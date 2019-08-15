"""
Test obo_parser
"""
import unittest
import os 
import sys
import json
sys.path.append('../')
import obo_parser

class TestOboParser(unittest.TestCase):
    def test_read_GO_obo_file(self):
        """
        Test reading the GO ontology OBO file.
        """
        path = os.path.join(os.getcwd(), 'data', 'go.obo')
        with open(path, 'rt') as read_file: 
            go = obo_parser.read_obo(read_file)
            self.assertEqual(len(go), 47401)
            self.assertEqual(go.node["GO:0000016"]["name"], "lactase activity")
            self.assertEqual(go.node["GO:0000018"]["relationship"], ["regulates GO:0006310"])
            self.assertEqual(go.node["GO:0000019"]["intersection_of"], ["GO:0008150", "regulates GO:0006312"])
            self.assertEqual(go.node["GO:0000022"]["namespace"], "biological_process")
            self.assertTrue('EC:3.1.13' in go.node["GO:0000175"]["xref"])
            
    def test_read_obsolete_terms(self):
        """
        Test reading obsolete terms in the GO ontology OBO file.
        """
        path = os.path.join(os.getcwd(), 'data', 'go.obo')
        with open(path, 'rt') as read_file: 
            go = obo_parser.read_obo(read_file)
            self.assertEqual(go.node["GO:0000020"]["is_obsolete"], "true")
            self.assertRaises(KeyError, lambda: go.node["GO:0000022"]["is_obsolete"])
            self.assertEqual(go.node["GO:0000005"]["is_obsolete"], "true")
            self.assertEqual(go.node["GO:0000005"]["consider"], ["GO:0042254", "GO:0044183", "GO:0051082"])
            self.assertEqual(go.node["GO:0000174"]["is_obsolete"], "true")
            self.assertEqual(go.node["GO:0000174"]["replaced_by"], ["GO:0000750"])

if __name__ == '__main__':
    # Use this if running from command line
    unittest.main()
    # Use this if running from iPython notebook 
#     unittest.main(argv=['first-arg-is-ignored'], exit=False)