"""
Tests edges created from GO_parser
"""
import unittest
import os
import sys
import json
sys.path.append('../')

# Note 19/9/11: I'm not sure what these tests are actually testing. They just open existing
# JSON files and run asserts on their contents. They don't test the parser at all


def get_file_dir():
    return os.path.dirname(__file__)


class TestGOEdges(unittest.TestCase):
    def test_relationship_edges(self):
        """
        Test terms contain all given fields from the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_edges_relationship.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0000332__GO:0003720__part_of":
                    self.assertEqual(entry["from"], "GO_term/GO:0000332")
                    self.assertEqual(entry["to"], "GO_term/GO:0003720")
                    self.assertEqual(entry["relationship_type"], "part_of")
                if entry["from"] == "GO_term/GO:0000335":
                    self.assertEqual(entry["id"], "GO:0000335__GO:0006313__negatively_regulates")
                    self.assertEqual(entry["to"], "GO_term/GO:0006313")
                    self.assertEqual(entry["relationship_type"], "negatively_regulates")

    def test_isa_edges(self):
        """
        Test terms contain all given fields from the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_edges_isa.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0000077__GO:0031570__is_a":
                    self.assertEqual(entry["from"], "GO_term/GO:0000077")
                    self.assertEqual(entry["to"], "GO_term/GO:0031570")

    def test_intersection_edges(self):
        """
        Test terms contain all given fields from the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_edges_intersection_of.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0000082__GO:0044843__":
                    self.assertEqual(entry["from"], "GO_term/GO:0000082")
                    self.assertEqual(entry["to"], "GO_term/GO:0044843")
                    self.assertEqual(entry["intersection_type"], "")
                if entry["id"] == "GO:0000082__GO:0000278__part_of":
                    self.assertEqual(entry["from"], "GO_term/GO:0000082")
                    self.assertEqual(entry["to"], "GO_term/GO:0000278")
                    self.assertEqual(entry["intersection_type"], "part_of")

    def test_disjoint_edges(self):
        """
        Test terms contain all given fields from the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_edges_disjoint_from.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0044848__GO:0051179__disjoint_from":
                    self.assertEqual(entry["from"], "GO_term/GO:0044848")
                    self.assertEqual(entry["to"], "GO_term/GO:0051179")

    def test_replaced_edges(self):
        """
        Test terms contain all given fields from the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_edges_replaced_by.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0001723__GO:0005882__replaced_by":
                    self.assertEqual(entry["from"], "GO_term/GO:0001723")
                    self.assertEqual(entry["to"], "GO_term/GO:0005882")

    def test_consider_edges(self):
        """
        Test terms contain all given fields from the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_edges_consider.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0000211__GO:0005515__consider":
                    self.assertEqual(entry["from"], "GO_term/GO:0000211")
                    self.assertEqual(entry["to"], "GO_term/GO:0005515")


if __name__ == '__main__':
    # Use this if running from command line
    unittest.main()
    # Use this if running from iPython notebook
#     unittest.main(argv=['first-arg-is-ignored'], exit=False)
