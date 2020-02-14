"""
Tests terms created from GO_parser
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


class TestGOTerm(unittest.TestCase):
    def test_term_keys_exist(self):
        """
        Test terms contain all given fields from the GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_term.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0000145":
                    self.assertEqual(entry["name"], "exocyst")
                    self.assertRaises(KeyError, lambda: entry["alt_id"])
                    self.assertEqual(entry["namespace"], "cellular_component")
                    self.assertEqual(entry["def"], (
                        "\"A protein complex peripherally associated with the "
                        "plasma membrane that determines where vesicles dock and "
                        "fuse. At least eight complex components are conserved "
                        "between yeast and mammals.\" [GOC:cilia, PMID:15292201, "
                        "PMID:27243008, PMID:9700152]")
                    )
                    self.assertRaises(KeyError, lambda: entry["comment"])
                    self.assertRaises(KeyError, lambda: entry["subset"])
                    self.assertEqual(entry["synonym"], ["\"exocyst complex\" EXACT []", "\"Sec6/8 complex\" EXACT []"])
                    self.assertEqual(entry["xref"], ["Wikipedia:Exocyst"])
                    self.assertRaises(KeyError, lambda: entry["is_obsolete"])
                    self.assertRaises(KeyError, lambda: entry["created_by"])
                    self.assertRaises(KeyError, lambda: entry["creation_date"])
                if entry["id"] == "GO:0035567":
                    self.assertEqual(entry["name"], "non-canonical Wnt signaling pathway")
                    self.assertRaises(KeyError, lambda: entry["alt_id"])
                    self.assertEqual(entry["namespace"], "biological_process")
                    self.assertEqual(entry["def"], (
                        "\"The series of molecular signals initiated by binding "
                        "of a Wnt protein to a frizzled family receptor on the "
                        "surface of the target cell, followed by propagation of "
                        "the signal via effectors other than beta-catenin.\" "
                        "[GOC:signaling]")
                    )
                    self.assertEqual(entry["comment"], (
                        "This term should only be used when Wnt receptor "
                        "signaling occurs via a beta-catenin-independent route "
                        "but the downstream effectors are unknown. If the "
                        "downstream effectors are known, consider instead "
                        "annotating to one of the children, or requesting a new "
                        "term.")
                    )
                    self.assertRaises(KeyError, lambda: entry["subset"])
                    self.assertEqual(entry["synonym"], [
                        "\"beta-catenin-independent Wnt receptor signaling pathway\" EXACT [GOC:signaling]",
                        "\"non-canonical Wnt receptor signaling pathway\" EXACT []",
                        "\"non-canonical Wnt receptor signalling pathway\" EXACT [GOC:mah]",
                        "\"non-canonical Wnt-activated signaling pathway\" EXACT [GOC:signaling]"]
                    )
                    self.assertRaises(KeyError, lambda: entry["xref"])
                    self.assertRaises(KeyError, lambda: entry["is_obsolete"])
                    self.assertEqual(entry["created_by"], "rfoulger")
                    self.assertEqual(entry["creation_date"], "2010-07-23T02:26:01Z")

    def test_obsolete_terms(self):
        """
        Test obsolete terms are labeled obsolete in GO ontology OBO file.
        """
        path = os.path.join(get_file_dir(), 'data', 'GO_term.json')
        with open(path, 'rt') as json_file:
            json_files = []
            for data in json_file:
                json_files.append(json.loads(data))
            for entry in json_files:
                if entry["id"] == "GO:0000008":
                    self.assertTrue("obsolete" in entry["name"])
                    self.assertEqual(entry["is_obsolete"], "true")


if __name__ == '__main__':
    # Use this if running from command line
    # unittest.main()
    # Use this if running from iPython notebook
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
