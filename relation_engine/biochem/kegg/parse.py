"""
See https://www.kegg.jp/kegg/docs/dbentry.html for KEGG file formats

Usually the get_* function depends on its gen_* counterpart function.
But sometimes it's the other way around!
And sometimes the get_* functions depend on each other
"""
from collections import defaultdict
from enum import Enum
import functools
import json
import numpy as np
import os
import pandas as pd
import re
from typing import Union


from relation_engine.biochem.ec.help import (
    MAX_EC_NUM_DEPTH,
    ec_nums_to_edges,
    expand_internal_ec_nums,
    is_ec_num,
    norm_ec_num,
    get_ec_num_depth,
    get_ec_num_parent,
)
from src.utils.debug import dprint

KEGG_REACTIONS_FP = "data/kegg/reaction.tsv"
KEGG_COMPOUNDS_FP = "data/kegg/compound.tsv"
KEGG_ORTHOLOGY_FP = "data/kegg/ko.tsv"
KEGG_REACTION_FULL_FP = "data/kegg/reaction_full.txt"
KEGG_ORTHOLOGY_FULL_FP = "data/kegg/ko_full.txt"
KEGG_ENZYME_FULL_FP = "data/kegg/enzyme_full.txt"


###############################################################################
def get_kegg_reaction_ids(fp=KEGG_REACTIONS_FP):
    rxn_ids = [doc["id"] for doc in gen_kegg_reactions(fp)]
    return rxn_ids


###############################################################################
def get_kegg_compound_ids(fp=KEGG_COMPOUNDS_FP):
    cpd_ids = [doc["id"] for doc in gen_kegg_compounds(fp)]
    return cpd_ids


###############################################################################
def get_kegg_orthology_ids(fp=KEGG_ORTHOLOGY_FP):
    df = pd.read_csv(fp, sep="\t", header=None)

    prefix = "ko:"

    ids = []
    for row in df.iterrows():
        _, rowdat = row[0], row[1].tolist()
        ids.append(rowdat[0][len(prefix):])  # strip prefix "ko:"

    return ids


###############################################################################
def get_kegg_leaf_ec_number_ids(fp=KEGG_ENZYME_FULL_FP):
    """
    All EC numbers from KEGG Enzyme are well behaved and of format: (\d+\.){3}(\d+)
    """
    df_enz = KEGGParse.get_enz_df(fp=fp)
    ec_num_leaves = [entry["id"] for entry in df_enz["ENTRY"]]

    # Sanity check on leaf EC numbers
    for ec_num in ec_num_leaves:
        assert is_ec_num(ec_num)
        assert ec_num == norm_ec_num(ec_num)
        assert get_ec_num_depth(ec_num) == MAX_EC_NUM_DEPTH

    return ec_num_leaves


###############################################################################
def get_kegg_edge_ids(fp=KEGG_ENZYME_FULL_FP):
    return ec_nums_to_edges(get_kegg_leaf_ec_number_ids(fp=fp))


###################################################################################################
###################################################################################################
def gen_kegg_ec_numbers(fp=KEGG_ENZYME_FULL_FP):
    df_enz = KEGGParse.get_enz_df(fp)
    columns = df_enz.columns.tolist()

    # Sanity check on leaf EC numbers
    ec_num_leaves = [entry["id"] for entry in df_enz["ENTRY"]]
    for ec_num in ec_num_leaves:
        assert is_ec_num(ec_num)
        assert ec_num == norm_ec_num(ec_num)
        assert get_ec_num_depth(ec_num) == MAX_EC_NUM_DEPTH

    # Yield leaf EC numbers
    for row in df_enz.iterrows():
        _, rowdat = row[0], row[1].tolist()

        yield {
            # Split first column into two fields
            "id": rowdat[0]["id"],
            "is_obsolete": rowdat[0]["is_obsolete"],
            # Rest of columns 1-1 as fields
            **dict(
                zip(columns[1:], rowdat[1:])
            ),
            # Will be either KEGG, ModelSEED, or null (for internal nodes)
            "source": "KEGG",
            # Will be popped
            "_collection": "EC_number",
        }

    # Yield internal EC numbers
    for ec_num in expand_internal_ec_nums(ec_num_leaves, return_new=True):

        yield {
            "id": ec_num,
            # Will be either KEGG, ModelSEED, or null (for internal nodes)
            "source": None,
            # Will be popped
            "_collection": "EC_number",
        }


###################################################################################################
###################################################################################################
def gen_kegg_ec_edges(fp=KEGG_ENZYME_FULL_FP):
   for ec_num_child, ec_num_parent in get_kegg_edge_ids(fp):
        yield {
            "id": f"{ec_num_child}@{ec_num_parent}",
            "from": ec_num_child,
            "to": ec_num_parent,
            # Will be popped
            "_collection": "EC_edge",
        }


###################################################################################################
###################################################################################################
def gen_kegg_reactions(fp=KEGG_REACTIONS_FP):
    df_rxn = pd.read_csv(fp, sep="\t", header=None)

    prefix = "rn:"
    dlm = ";"

    for row in df_rxn.iterrows():
        _, rowdat = row[0], row[1].tolist()
        yield {
            "id": rowdat[0][len(prefix):],  # strip prefix "rn:"
            "names": rowdat[1].split(dlm),
        }


###################################################################################################
###################################################################################################
def gen_kegg_compounds(fp=KEGG_COMPOUNDS_FP):
    df = pd.read_csv(fp, sep="\t", header=None)

    prefix = "cpd:"
    dlm = ";"

    for row in df.iterrows():
        _, rowdat = row[0], row[1].tolist()
        yield {
            "id": rowdat[0][len(prefix):],  # strip prefix "cpd:"
            "names": rowdat[1].split(dlm),
        }


###################################################################################################
###################################################################################################
def gen_kegg_orthology(fp=KEGG_ORTHOLOGY_FULL_FP):
    df = KEGGParse.get_ort_df(fp=fp)
    df = df.rename(lambda col_name: col_name.lower(), axis=1).rename(columns={"entry": "id"})
    columns = df.columns.tolist()

    for row in df.iterrows():
        _, rowdat = row[0], row[1].tolist()

        yield dict(
            zip(
                columns, rowdat
            )
        )


########################################################################################################################
########################################################################################################################
def gen_kegg_enzyme_to_orthology(fp=KEGG_ENZYME_FULL_FP):
    df_enz = KEGGParse.get_enz_df(fp=fp)

    SELF_COLL = "EC_number"
    XREF_COLL = "KEGG_orthology"

    for row in df_enz.iterrows():
        _, rowdat = row[0], row[1]

        ec_num, ko_id_name = rowdat["ENTRY"]["id"], rowdat["ORTHOLOGY"]

        if ko_id_name is not None:
            ko_id = ko_id_name["id"]
            ko_name = ko_id_name["name"]

            yield {
                "id": f"{ec_num}@{XREF_COLL}@{ko_id}",
                "name": ko_name,
                "xref_coll": XREF_COLL,
                "is_alias": 0,
                # Will have coll name parsed out (from/to)
                "from": f"{SELF_COLL}/{ec_num}",
                "to": f"{XREF_COLL}/{ko_id}",
                # Will be popped
                "_collection": "EC_number_xref",
                "_is_xref": 1,
            }


########################################################################################################################
########################################################################################################################
def gen_kegg_reaction_to_orthology(fp=KEGG_REACTION_FULL_FP):
    df_rxn = KEGGParse.get_rxn_df(fp=fp)

    SELF_COLL = "KEGG_reaction"
    XREF_COLL = "KEGG_orthology"

    for row in df_rxn.iterrows():
        _, rowdat = row[0], row[1]

        rxn_id, ko_id_names = rowdat["ENTRY"], rowdat["ORTHOLOGY"]
        
        if ko_id_names is not None:
            for ko_id_name in ko_id_names:

                ko_id = ko_id_name["id"]
                ko_name = ko_id_name["name"]

                # Sanity check
                # TODO check in KO IDs
                assert re.match(r"K\d{5}", ko_id)
                assert re.match(r".+", ko_name)

                yield {
                    "id": f"{rxn_id}@{XREF_COLL}@{ko_id}",
                    "name": ko_name,
                    # Will name collection parsed out
                    "from": f"{SELF_COLL}/{rxn_id}",
                    "to": f"{XREF_COLL}/{ko_id}",
                    # Will be popped
                    "_is_xref": 1,
                    "_collection": "KEGG_reaction_xref",
                }


###############################################################################
###############################################################################
class KEGGParse:
    RECORD_END = "///"

    @staticmethod
    def canonicalize_none_or_single_item(dat):
        if dat is None:
            return None
        assert isinstance(dat, list)
        assert len(dat) == 1

        dat = dat[0]

        return dat

    @staticmethod
    def canonicalize_none_or_multi_item(dat):
        """
            [
                ['long-chain acyl-CoA dehydrogenase;'],
                ['very-long-chain acyl-CoA dehydrogenase;'],
                None,
                ['cyclohex-1-ene-1-carbonyl-CoA dehydrogenase'],
                ['cyclohexane-1-carbonyl-CoA dehydrogenase (electron-transfer flavoprotein);'],
                ['(2S)-methylsuccinyl-CoA dehydrogenase;', 'Mcd'],
                ...
            ]
        """
        if dat is None:
            return []
        assert isinstance(dat, list)
        assert len(dat) > 0

        dat = [product.strip(";") for product in dat]

        return dat

    @staticmethod
    def canonicalize_none_or_tup_str(dat, max_split=-1):
        if dat is None:
            return None
        assert isinstance(dat, list)
        assert len(dat) == 1

        dat = dat[0]
        dat = dat.split(None, max_split)

        return dat

    @staticmethod
    def canonicalize_none_or_single_id_name(dat):
        if dat is None:
            return None
        assert isinstance(dat, list)
        assert len(dat) == 1

        dat = dat[0]
        
        return dict(
            zip(
                ("id", "name"),
                dat.split(None, 1)
            )
        )

    @staticmethod
    def canonicalize_none_or_multi_id_name(dat):
        if dat is None:
            return []
        assert isinstance(dat, list)
        assert len(dat) > 0

        dat = [
            dict(
                zip(
                    ("id", "name"),
                    line.split(None, 1)
                )
            )
            for line in dat
        ]
        
        return dat


    ####################
    ####################
    class Reaction:
        
        @staticmethod
        def canonicalize_rxn_entry(dat):
            """
            [
                ['R01177                      Reaction'],
                ['R01178                      Reaction'],
                ['R01179                      Reaction'],
                ...
            ]
            """
            # No Nones actually
            return KEGGParse.canonicalize_none_or_tup_str(dat)[0]

        @staticmethod
        def canonicalize_rxn_name(dat):
            """
            [
                ['1D-myo-inositol 4-phosphate phosphohydrolase'],
                ['1D-myo-inositol 3-phosphate phosphohydrolase'],
                None,
                [
                    'Propanoyl-CoA:acetyl-CoA C-acyltransferase;',
                    '3alpha,7alpha-dihydroxy-5beta-cholanoyl-CoA:propanoyl-CoA;',
                    'C-acyltransferase'
                ]
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_multi_item(dat)


        @staticmethod
        def canonicalize_rxn_orthology(dat):
            """
            [
                None,
                ['K00010  myo-inositol 2-dehydrogenase / D-chiro-inositol 1-dehydrogenase [EC:1.1.1.18 1.1.1.369]'],
                ['K00469  inositol oxygenase [EC:1.13.99.1]'],
                [
                    'K01092  myo-inositol-1(or 4)-monophosphatase [EC:3.1.3.25]',
                    'K10047  inositol-phosphate phosphatase / L-galactose 1-phosphate phosphatase [EC:3.1.3.25 3.1.3.93]',
                    'K18649  inositol-phosphate phosphatase / L-galactose 1-phosphate phosphatase / histidinol-phosphatase [EC:3.1.3.25 3.1.3.93 3.1.3.15]'
                ],
            ]
            """
            return KEGGParse.canonicalize_none_or_multi_id_name(dat)


    ####################
    ####################
    class Orthology:

        @staticmethod
        def canonicalize_ort_entry(dat):
            """
            [
                ['K00001                      KO'],
                ['K00002                      KO'],
                ['K00003                      KO'],
                ['K00004                      KO'],
                ['K00005                      KO'],
                ['K00006                      KO'],
                ['K00492            Tight     KO'],
                ...
            ]
            """
            assert isinstance(dat, list)
            assert len(dat) == 1
            assert len(dat[0].split()) >= 2, dat
            
            dat = dat[0]
            id = dat.split(None, 1)[0]

            return id

        @staticmethod
        def canonicalize_ort_symbol(dat):
            """
            [
                ['E1.1.1.1, adh'],
                ['AKR1A1, adh'],
                ['hom'],
                ['BDH, butB'],
                ['gldA'],
                ['GPD1'],
                ...
            ]
            """
            if dat is None:
                return []
            assert isinstance(dat, list)
            assert len(dat) == 1

            dat = dat[0]
            dat = [tok.strip() for tok in dat.split(",")]

            return dat

        @staticmethod
        def canonicalize_ort_name(dat):
            """
            [
                ['alcohol dehydrogenase [EC:1.1.1.1]'],
                ['alcohol dehydrogenase (NADP+) [EC:1.1.1.2]'],
                ['homoserine dehydrogenase [EC:1.1.1.3]'],
                ['(R,R)-butanediol dehydrogenase / meso-butanediol dehydrogenase / diacetyl reductase [EC:1.1.1.4 1.1.1.- 1.1.1.303]'],
                ['glycerol dehydrogenase [EC:1.1.1.6]'],
                ['fumarate reductase subunit C'],
                ['fumarate reductase subunit D'],
                ...
            ]
            """
            # No Nones, but doesn't matter
            return KEGGParse.canonicalize_none_or_single_item(dat)

        @staticmethod
        def canonicalize_ort_pathway(dat):
            """
            [
                [
                    'map00650  Butanoate metabolism',
                    'map01110  Biosynthesis of secondary metabolites'
                ],
                [
                    'map00561  Glycerolipid metabolism',
                    'map00640  Propanoate metabolism',
                    'map01100  Metabolic pathways'
                ],
                None,
                ['map05202  Transcriptional misregulation in cancer'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_multi_id_name(dat)

        @staticmethod
        def canonicalize_ort_module(dat):
            """
            [
                [
                    'M00003  Gluconeogenesis, oxaloacetate => fructose-6P',
                    'M00165  Reductive pentose phosphate cycle (Calvin cycle)',
                    'M00167  Reductive pentose phosphate cycle, glyceraldehyde-3P => ribulose-5P'
                ],
                None,
                ['M00026  Histidine biosynthesis, PRPP => histidine']
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_multi_id_name(dat)

        @staticmethod
        def canonicalize_ort_reference(dat):
            """
            [
                ...
            ]
            """
            if dat is None:
                return None
            assert isinstance(dat, list)
            assert len(dat) > 0

            pmid = re.search(r"PMID:\d+", dat[0])

            if pmid:
                return pmid[0]
            else:
                return None

    ####################
    ####################
    class Enzyme:

        @staticmethod
        def canonicalize_enz_entry(dat):
            """
            [
                ['EC 1.1.1.66                 Enzyme'],
                ['EC 1.1.1.67                 Enzyme'],
                ['EC 1.1.1.68       Obsolete  Enzyme'],
                ['EC 1.1.1.69                 Enzyme'],
                ['EC 1.1.1.70       Obsolete  Enzyme'],
                ...
            ]
            """
            assert isinstance(dat, list)
            assert len(dat) == 1
            assert len(dat[0].split()) in [3, 4]
            
            dat = dat[0]
            _, ec_num, is_obsolete = dat.split(None, 2)
            is_obsolete = "Obsolete" in is_obsolete

            return {"id": ec_num, "is_obsolete": is_obsolete}

        @staticmethod
        def canonicalize_enz_name(dat):
            """
            [
                ['long-chain acyl-CoA dehydrogenase;'],
                ['very-long-chain acyl-CoA dehydrogenase;'],
                ['cyclohex-1-ene-1-carbonyl-CoA dehydrogenase'],
                ['cyclohexane-1-carbonyl-CoA dehydrogenase (electron-transfer flavoprotein);'],
                ['(2S)-methylsuccinyl-CoA dehydrogenase;', 'Mcd'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_multi_item(dat)


        @staticmethod
        def canonicalize_enz_class(dat):
            """
            [
                ['Oxidoreductases;'],
                ['Transferases;', 'Acyltransferases;'],
                ...
            ]
            """
            # No Nones, but doesn't matter
            return KEGGParse.canonicalize_none_or_multi_item(dat)


        @staticmethod
        def canonicalize_enz_sysname(dat):
            """
            [
                ['L-aspartate:oxygen oxidoreductase'],
                None,
                None,
                ['glycine:oxygen oxidoreductase (deaminating)'],
                ['L-lysine:oxygen 6-oxidoreductase (deaminating)'],
                ['primary-amine:oxygen oxidoreductase (deaminating)'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_single_item(dat)


        @staticmethod
        def canonicalize_enz_reaction(dat):
            """
            [
                None,
                None,
                ['glycine + H2O + O2 = glyoxylate + NH3 + H2O2 (overall reaction) [RN:R00366];'],
                ['L-lysine + O2 + H2O = (S)-2-amino-6-oxohexanoate + H2O2 + NH3 [RN:R07598]'],
                ['RCH2NH2 + H2O + O2 = RCHO + NH3 + H2O2 [RN:R01853]'],
                ['histamine + H2O + O2 = (imidazol-4-yl)acetaldehyde + NH3 + H2O2 [RN:R02150]'],
                ['7-chloro-L-tryptophan + O2 = 2-imino-3-(7-chloroindol-3-yl)propanoate + H2O2 [RN:R09560]'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_single_item(dat)

        @staticmethod
        def canonicalize_enz_substrate(dat):
            """
            [
                None,
                ['L-valine [CPD:C00183];'],
                ['glutathione [CPD:C00051];', 'hydroperoxy-fatty-acyl-[lipid]'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_multi_item(dat)

        @staticmethod
        def canonicalize_enz_product(dat):
            """
            [
                ['5-guanidino-2-oxopentanoate [CPD:C03771];'],
                ['5-[(4-hydroxyphenyl)methyl]-4,4-dimethylpyrrolidine-2,3-dione [CPD:C22331];'],
                None,
                ['pyranos-2-ulose;', 'pyranos-3-ulose;', 'pyranos-2,3-diulose;'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_multi_item(dat)


        @staticmethod
        def canonicalize_enz_comment(dat):
            return KEGGParse.canonicalize_none_or_single_item(dat)

        @staticmethod
        def canonicalize_enz_pathway(dat):
            """
            [
                ['ec00330  Arginine and proline metabolism'],
                None,
                None,
                ['ec00260  Glycine, serine and threonine metabolism'],
                ['ec00360  Phenylalanine metabolism'],
                ['ec00630  Glyoxylate and dicarboxylate metabolism'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_single_id_name(dat)

        @staticmethod
        def canonicalize_enz_orthology(dat):
            """
            [
                ['K24693  pre-mycofactocin synthase'],
                None,
                ['K00281  glycine dehydrogenase'],
                ['K00285  D-amino-acid dehydrogenase'],
                ['K00284  glutamate synthase (ferredoxin)'],
                ...
            ]
            """
            return KEGGParse.canonicalize_none_or_single_id_name(dat)

        @staticmethod
        def canonicalize_enz_reference(dat):
            """
            [
                None,
                None,
                ['1  [PMID:11744710]', '2  [PMID:9827558]'],
                ['1  [PMID:16547036]', '2  [PMID:17030025]'],
                [
                    '1  [PMID:7337701]',
                    '2  [PMID:7622512]',
                    '3  [PMID:8920635]',
                    '4  [PMID:9405045]',
                    '5  [PMID:9677370]',
                    '6  [PMID:10668504]',
                    '7  [PMID:11156689]',
                    '8  [PMID:11985492]',
                    '9  [PMID:14697905]',
                    '10 [PMID:16046623]'
                ],
                ['1', '2  [PMID:320001]', '3', '4', '5  [PMID:13605979]'],
                ['1'],
                ...
            ]
            """
            if dat is None:
                return []
            assert isinstance(dat, list)
            assert len(dat) > 0

            ids = [
                re.search(r"PMID:\d+", ref)[0]
                for ref in dat
                if re.search(r"PMID:\d+", ref)
            ]

            return ids

    ####################
    ####################
    def __init__(
        self,
        fp,
        columns,
        ignore_columns=[],
    ):
        """
        Parameters
        ----------
        
        :fp:                file path to KEGG formatted file
        :columns:           names of the fields you want in the KEGG formatted file
        :ignore_columns:    names of the fields you want to ignore in the KEGG formatted file
        """
        self.fp = fp
        self.columns = [col for col in columns if col not in ignore_columns]

    def gen_records(self):
        """Iterate through lines of KEGG formatted file
        recording all the lines each time the end-of-record symbol is encountered
        """
        with open(self.fp) as fh:
            record = []
            for line in fh:
                line = line.strip("\n")
                if line != self.RECORD_END:
                    record.append(line)
                else:
                    yield record
                    record = []

    def get_field(self, line):
        """See if line from a KEGG formatted file has a field and data,
        separated by whitespace
        """
        match = re.match(r"^(\S+)\s+(.+)", line)
        if match:
            return match[1], match[2]
        else:
            return None

    def record_2_row(self, record):
        """
        Record should come in as a list of lines for that record
        from the KEGG formatted file

        :return:    a dict keyed with fields and valued with a list of lines
        """
        assert isinstance(record, list)
        assert len(record) > 0

        row = defaultdict(list)

        for line in record:

            line = line.strip()

            if self.get_field(line):
                field, dat = self.get_field(line)
            else:
                dat = line

            if field in self.columns:  # only keep fields we wang
                row[field].append(dat.strip())

        return row

    ####################
    def to_df(self, stop=-1):
        df = pd.DataFrame(columns=self.columns)
        for i, record in enumerate(self.gen_records()):
            if i == stop:
                break
            row_dic = self.record_2_row(record)
            row_df = pd.DataFrame([row_dic])
            df = pd.concat([df, row_df], ignore_index=True)
        return df.replace({np.nan: None})


    ####################
    ####################
    @classmethod
    @functools.cache
    def get_rxn_df(
        cls,
        fp=KEGG_REACTION_FULL_FP,
        columns=[
            "ENTRY",
            "NAME",
            "ORTHOLOGY",
        ],
        stop=-1
    ):
        df = cls(fp, columns).to_df(stop=stop)

        df["ENTRY"] = df["ENTRY"].apply(lambda dat: cls.Reaction.canonicalize_rxn_entry(dat))
        df["NAME"] = df["NAME"].apply(lambda dat: cls.Reaction.canonicalize_rxn_name(dat))
        df["ORTHOLOGY"] = df["ORTHOLOGY"].apply(lambda dat: cls.Reaction.canonicalize_rxn_orthology(dat))

        return df

    ####################
    ####################
    @classmethod
    @functools.cache
    def get_ort_df(
        cls,
        fp=KEGG_ORTHOLOGY_FULL_FP,
        columns=[
            "ENTRY",
            "SYMBOL",
            "NAME",
            "PATHWAY",
            "MODULE",
            "NETWORK",
            "DISEASE",
            "BRITE",
            "DBLINKS",
            "GENES",
            "REFERENCE",
        ],
        ignore_columns=[
            "NETWORK",  # empty for orthology
            "DISEASE",
            "BRITE",
            "DBLINKS",
            "GENES",
        ],
        stop=-1,
    ):

        df = cls(fp, columns, ignore_columns).to_df(stop=stop)

        df["ENTRY"] = df["ENTRY"].apply(lambda dat: cls.Orthology.canonicalize_ort_entry(dat))
        df["SYMBOL"] = df["SYMBOL"].apply(lambda dat: cls.Orthology.canonicalize_ort_symbol(dat))
        df["NAME"] = df["NAME"].apply(lambda dat: cls.Orthology.canonicalize_ort_name(dat))
        df["PATHWAY"] = df["PATHWAY"].apply(lambda dat: cls.Orthology.canonicalize_ort_pathway(dat))
        df["MODULE"] = df["MODULE"].apply(lambda dat: cls.Orthology.canonicalize_ort_module(dat))
        df["REFERENCE"] = df["REFERENCE"].apply(lambda dat: cls.Orthology.canonicalize_ort_reference(dat))

        return df

    ####################
    ####################
    @classmethod
    @functools.cache
    def get_enz_df(
        cls,
        fp=KEGG_ENZYME_FULL_FP,
        columns=[
            'ENTRY',
            'NAME',
            'CLASS',
            'SYSNAME',
            'REACTION',
            'ALL_REAC',
            'SUBSTRATE',
            'PRODUCT',
            'COMMENT',
            'PATHWAY',
            'ORTHOLOGY',
            'GENES',
            'REFERENCE',
            'DBLINKS'
        ],
        ignore_columns=[
            "ALL_REAC",  # dunno how to parse
            "DISEASE",
            "BRITE",
            "DBLINKS",
            "GENES",
        ],
        stop=-1,
    ):

        df = cls(fp, columns, ignore_columns).to_df(stop=stop)

        df["ENTRY"] = df["ENTRY"].apply(lambda dat: cls.Enzyme.canonicalize_enz_entry(dat))
        df["NAME"] = df["NAME"].apply(lambda dat: cls.Enzyme.canonicalize_enz_name(dat))
        df["CLASS"] = df["CLASS"].apply(lambda dat: cls.Enzyme.canonicalize_enz_class(dat))
        df["SYSNAME"] = df["SYSNAME"].apply(lambda dat: cls.Enzyme.canonicalize_enz_sysname(dat))
        df["REACTION"] = df["REACTION"].apply(lambda dat: cls.Enzyme.canonicalize_enz_reaction(dat))
        df["SUBSTRATE"] = df["SUBSTRATE"].apply(lambda dat: cls.Enzyme.canonicalize_enz_substrate(dat))
        df["PRODUCT"] = df["PRODUCT"].apply(lambda dat: cls.Enzyme.canonicalize_enz_product(dat))
        df["COMMENT"] = df["COMMENT"].apply(lambda dat: cls.Enzyme.canonicalize_enz_comment(dat))
        df["PATHWAY"] = df["PATHWAY"].apply(lambda dat: cls.Enzyme.canonicalize_enz_pathway(dat))
        df["ORTHOLOGY"] = df["ORTHOLOGY"].apply(lambda dat: cls.Enzyme.canonicalize_enz_orthology(dat))
        df["REFERENCE"] = df["REFERENCE"].apply(lambda dat: cls.Enzyme.canonicalize_enz_reference(dat))

        return df
