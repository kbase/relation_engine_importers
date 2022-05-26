"""
Parse/wrangle SILVA SSU taxonomy file

Ranks are:
{'root_rank', 'sequence'} +
{'superfamily', 'subphylum', 'subfamily', 'phylum', 'order', 'major_clade', 'infraclass',
'suborder', 'family', 'superkingdom', 'domain', 'superphylum', 'superorder', 'superclass',
'infraphylum', 'subclass', 'genus', 'class', 'kingdom', 'subkingdom'}
"""
import pandas as pd
import numpy as np
import logging
from Bio import SeqIO
import os
import time

from relation_engine.taxa.silva.util.dprint import dprint

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(name)s:%(levelname)s: %(message)s"
)


ROOT_NAME = "Root"  # SILVA does not set this, so arbitrarily chosen
ROOT_RANK = "root_rank"  # SILVA does not set this, so arbitrarily chosen
ROOT_TAXID = 0  # SILVA does not set this, so arbitrarily chosen (0 not taken)


class SILVANodeProvider:
    """
    Required: id, name rank
    """

    def __iter__(self):
        for taxnode in TaxNode.instances.values():
            node = {
                "id": str(taxnode.taxid),
                "name": taxnode.name,
                "rank": taxnode.rank,
            }

            # Root, Archaea, etc. don't have release
            if taxnode.release is not None:
                node["release"] = taxnode.release

            yield (node)

        for seqnode in SeqNode.instances.values():
            yield {
                "id": seqnode.id,
                "name": seqnode.organism_name,
                "rank": "sequence",
                "sequence": seqnode.seq,
                "datasets": seqnode.datasets,
            }


class SILVAEdgeProvider:
    def __iter__(self):
        for taxnode in TaxNode.instances.values():
            if taxnode.parent is not None:
                yield {
                    "id": str(taxnode.taxid),
                    "from": str(taxnode.taxid),
                    "to": str(taxnode.parent.taxid),
                }
        for seqnode in SeqNode.instances.values():
            yield {
                "id": seqnode.id,
                "from": seqnode.id,
                "to": str(TaxNode.instances[seqnode.taxpath].taxid),
            }


do_parc = True
do_ref = True
do_nr99 = True
do_check_assumptions = False


class SeqNode:

    instances = dict()

    def __init__(self, acs, start, stop, taxpath, organism_name, seq, dataset):
        """
        acs, start, stop - INSDC primary accession, start position within the rRNA entry, and
            stop position within the rRNA entry. "different
            rRNA regions of the same INSDC entry (genome) may be assigned to multiple
            paths" (SILVA)
        """
        id = ".".join([acs, start, stop])

        self.id = id
        self.acs = acs
        self.start = int(start)
        self.stop = int(stop)
        self.taxpath = taxpath
        self.organism_name = organism_name
        self.seq = seq
        self.datasets = [dataset]

        if id in self.instances:
            assert self == self.instances[id]
            self.instances[id].datasets.append(dataset)
        else:
            self.instances[id] = self

    # TODO are taxids in acc_taxid/taxmap different from taxfile taxids? what about the rest of the info?

    @classmethod
    def parse_fastas(cls, dir):

        cls.instances.clear()

        parc_fasta_flpth = os.path.join(dir, "SILVA_138_SSUParc_tax_silva.fasta")
        ref_fasta_flpth = os.path.join(dir, "SILVA_138_SSURef_tax_silva.fasta")
        nr99_fasta_flpth = os.path.join(dir, "SILVA_138_SSURef_NR99_tax_silva.fasta")

        def add_node(record, dataset):
            acs, start, stop = record.name.split(".")
            taxpath = (
                ";".join(record.description.split(" ", 1)[1].split(";")[:-1]) + ";"
            )
            organism_name = record.description.split(" ", 1)[1].split(";")[-1]
            seq = str(record.seq)

            cls(acs, start, stop, taxpath, organism_name, seq, dataset)

        if do_parc:
            logging.info("Parsing %s" % parc_fasta_flpth)
            t0 = time.time()

            for i, record in enumerate(SeqIO.parse(parc_fasta_flpth, "fasta")):
                add_node(record, "parc")

            logging.info(
                "Parsed %d records. Took %.2fmin" % ((i + 1), (time.time() - t0) / 60)
            )

        if do_ref:
            logging.info("Parsing %s" % ref_fasta_flpth)
            t0 = time.time()

            for i, record in enumerate(SeqIO.parse(ref_fasta_flpth, "fasta")):
                add_node(record, "ref")

            logging.info(
                "Parsed %d records. Took %.2fmin" % ((i + 1), (time.time() - t0) / 60)
            )

        if do_nr99:
            logging.info("Parsing %s" % nr99_fasta_flpth)
            t0 = time.time()

            for i, record in enumerate(SeqIO.parse(nr99_fasta_flpth, "fasta")):
                add_node(record, "nr99")

            logging.info(
                "Parsed %d records. Took %.2fmin" % ((i + 1), (time.time() - t0) / 60)
            )

        if do_check_assumptions and do_ref and do_nr99:
            cls._check_assumptions()

    @classmethod
    def _check_assumptions(cls):

        # expected num ref and nr99

        NUM_NR99 = 510984
        NUM_REF = 2225272

        assert len(cls.instances) == NUM_REF, "num instances: %d, num ref: %d" % (
            len(cls.instances),
            NUM_REF,
        )
        assert (
            len(
                [
                    True
                    for seqnode in cls.instances.values()
                    if "nr99" in seqnode.dataset
                ]
            )
            == NUM_NR99
        )

        # hist seq lengths

        # uniqueness in ref

        num_ref = len(cls.instances)
        acs = [seqnode.acs for seqnode in cls.instances.values()]
        taxpaths = [seqnode.taxpath for seqnode in cls.instances.values()]
        organism_names = [seqnode.organism_name for seqnode in cls.instances.values()]
        seqs = [seqnode.seq for seqnode in cls.instances.values()]

        dprint(
            "NUM_REF",
            "num_ref",
            "len(set(acs))",
            "len(set(taxpaths))",
            "len(set(organism_names))",
            "len(set(seqs))",
            "discrete_hist(acs)",
            "discrete_hist(taxpaths)",
            "discrete_hist(organism_names)",
            "discrete_hist(seqs)",
            run={**globals(), **locals()},
            max_lines=20,
        )

        # uniqueness in nr99

        num_nr99 = sum(
            [1 for seqnode in cls.instances.values() if "nr99" in seqnode.dataset]
        )
        acs = [
            seqnode.acs
            for seqnode in cls.instances.values()
            if "nr99" in seqnode.dataset
        ]
        taxpaths = [
            seqnode.taxpath
            for seqnode in cls.instances.values()
            if "nr99" in seqnode.dataset
        ]
        organism_names = [
            seqnode.organism_name
            for seqnode in cls.instances.values()
            if "nr99" in seqnode.dataset
        ]
        seqs = [
            seqnode.seq
            for seqnode in cls.instances.values()
            if "nr99" in seqnode.dataset
        ]

        dprint(
            "NUM_NR99",
            "num_nr99",
            "len(set(acs))",
            "len(set(taxpaths))",
            "len(set(organism_names))",
            "len(set(seqs))",
            "discrete_hist(acs)",
            "discrete_hist(taxpaths)",
            "discrete_hist(organism_names)",
            "discrete_hist(seqs)",
            run={**globals(), **locals()},
            max_lines=20,
        )

        # parent taxpaths exist

        for seqnode in cls.instances.values():
            TaxNode.instances[seqnode.taxpath]  # shouldn't throw

    def __eq__(self, other):
        """
        Check if all fields, except `dataset`, equal
        """
        return (
            self.id == other.id
            and self.acs == other.acs
            and self.start == other.start
            and self.stop == other.stop
            and self.taxpath == other.taxpath
            and self.organism_name == other.organism_name
            and self.seq == other.seq
        )


class TaxNode:
    """
    Make node for each taxon,
    store path/node as key/value pair in class var `instances`.

    Probably not the most resource frugal implementation

    Recycled from script parsing SILVA taxfile,
    doing sanity checks,
    and formatting into RDP Classifier `train` input taxfile
    """

    instances = {}  # path to `TaxNode` instance dict
    # paths are taken verbatim from taxonomy file
    # paths begin at domain and follow pattern (Taxname;)+
    # note: 'Root' is an exception to all above since it's not in the taxonomy file

    taxids = []  # debug

    def __init__(self, path, taxid, rank, release):
        """
        Root comes in, artificially, as ('Root', 0, 'rootrank', np.nan)
        Everything else comes in from tax_slv_ssu_138.txt as (\(Taxname;\)\+, \d+, 'rank', \d+.0|np.nan)  # noqa W605
        """
        self.path = path  # begins with domain
        self.taxid = int(
            taxid
        )  # mostly stable in 138+ releases. all taxa have this value
        self.rank = rank  # all taxa have this value
        self.release = (
            None if np.isnan(release) else int(release)
        )  # root and the three domains and don't have this value

        #
        self.instances[path] = self

        # debug
        self.taxids.append(taxid)

    @property
    def depth(self):
        """Root is depth 0"""
        return self.path.count(";")

    @property
    def name(self):
        if self.depth == 0:
            return ROOT_NAME
        elif self.depth > 0:
            return self.path.split(";")[-2]  # paths are semicolon-terminated
        else:
            raise Exception

    @property
    def parent(self):
        return (
            self.instances[self.parent_path] if self.parent_path is not None else None
        )

    @property
    def parent_path(self):
        """Used for `self.instances` lookup"""
        if self.depth == 0:  # root
            return None
        elif self.depth == 1:
            return "Root"
        elif self.depth > 1:
            return ";".join(self.path.split(";")[:-2]) + ";"
        else:
            raise Exception()

    @staticmethod
    def parse_taxfile(dir):

        flpth = os.path.join(dir, "tax_slv_ssu_138.txt")

        TaxNode.clear()  # TaxNode keeps static list of instances. clear before each taxfile

        logging.info("Parsing taxonomy file %s" % flpth)

        df = pd.read_csv(
            flpth,
            sep="\t",
            names=["path", "taxid", "rank", "remark", "release"],
            index_col=False,
        )

        dprint(
            "set(df['rank'].tolist())",
            "sorted(df['taxid'].tolist())[:30]",
            "sorted(df['taxid'].tolist())[-30:]",
            "[e for e in df['remark'].tolist() if not (type(e) == float and np.isnan(e))] # non-nan remarks",
            "set(df['release'].tolist())",
            run={**globals(), **locals()},
        )

        df.drop(["remark"], inplace=True, axis=1)

        dprint("df", run=locals())

        logging.info("Creating `TaxNode` for each taxon path")

        # create node for each taxon

        TaxNode(ROOT_NAME, ROOT_TAXID, ROOT_RANK, np.nan)  # taxid=0 is not taken

        for index, row in df.iterrows():
            TaxNode(row["path"], row["taxid"], row["rank"], row["release"])

        # debug

        assert len(set(TaxNode.taxids)) == len(TaxNode.taxids), list(
            zip(sorted(set(TaxNode.taxids)), sorted(TaxNode.taxids))
        )

        # there are external tests for taxonomy nodes

        return df

    @classmethod
    def clear(cls):
        """For testing different taxonomy files"""
        cls.instances = dict()
        cls.taxids = []


def discrete_hist(l, cutoff=10, max=100):

    """
    Return dict with elements in l as keys, counts as values, sorted by highest count
    Drop low cts
    """
    d = dict()

    for e in l:
        if e not in d:
            d[e] = 1
        else:
            d[e] += 1

    d = {
        k: v
        for i, (k, v) in enumerate(
            sorted(d.items(), key=lambda item: item[1], reverse=True)
        )
        if (max is None or i < max) and v > cutoff
    }

    return d


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(cwd, "test/data/full")

    TaxNode.parse_taxfile(input_dir)
    SeqNode.parse_fastas(input_dir)

    SeqNode._check_assumptions()


if __name__ == "__main__":

    main()
