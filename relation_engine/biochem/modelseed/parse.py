"""
LAST UPDATED: JUN 2022
PRECONDITION: Run download_modelseed.sh

Parse ModelSEED data files and provide vertices/edges in a generator


Reactions columns
-----------------
1.  id: Unique ID for the reaction in the format rxnNNNNN where NNNNN is
    a five digit number (e.g. rxn03789)
2.  abbreviation: Short name of reaction
3.  name: Long name of reaction
4.  code: Definition of reaction expressed using compound IDs and before
    protonation (see below for description of format)
5.  stoichiometry: Definition of reaction expressed in stoichiometry
    format (see below for description of format)
6.  is_transport: True if reaction is a transport reaction
7.  equation: Definition of reaction expressed using compound IDs and
    after protonation (see below for description of format)
8.  definition: Definition of reaction expressed using compound names
    (see below for description of format)
9.  reversibility: Reversibility of reaction where “>” means right
    directional, “<” means left directional, “=” means bi-directional,
    and “?” means unknown (Need a better description of reversibility
    and direction)
10. direction: Direction of reaction where “>” means right directional,
    “<” means left directional, and “=” means bi-directional
11. abstract_reaction: Need definition or “null” if not specified
    (currently all reactions are set to null)
12. pathways: Pathways reaction is a part of or “null” if not specified
    (currently all reactions are set to null)
13. aliases: List of alternative names of reaction separated by
    semicolon or “null” if not specified (format is the same as
    Compounds file)
14. ec_numbers: Enzyme Commission numbers of enzymes that catalyze
    reaction or “null” if not specified (currently all reactions are set
    to null)
15. deltag: Value for change in free energy of reaction or 10000000 when
    unknown
16. deltagerr: Value for change in free energy error of reaction or
    10000000 when unknown
17. compound_ids: List of compound IDs separated by semicolon for
    compounds involved in reaction
18. status: String describing status of the reaction with multiple
    values delimited with a “|” character. See below for details.
19. is_obsolete: True if reaction is obsolete and replaced by different
    reaction
20. linked_reaction: List of reaction IDs separated by semicolon related
    to this reaction or “null” if not specified (used to link an
    obsolete reaction to replacement reaction)
21. notes: Abbreviated notation used to store derived information about
    the reaction
22. source: Source database of reaction (currently only source is
    ModelSEED)


Aliase namespaces are
---------------------
{'AlgaGEM',
 'AraCyc',
 'AraGEM',
 'BiGG',
 'BrachyCyc',
 'ChlamyCyc',
 'CornCyc',
 'EcoCyc',
 'KEGG',
 'MaizeCyc',
 'MetaCyc',
 'Name',
 'PlantCyc',
 'PoplarCyc',
 'RiceCyc',
 'SorghumCyc',
 'SoyCyc',
 'iAF1260',
 'iAF692',
 'iAG612',
 'iAO358',
 'iAbaylyiv4',
 'iGT196',
 'iIN800',
 'iIT341',
 'iJN746',
 'iJR904',
 'iMA945',
 'iMEO21',
 'iMM904',
 'iMO1056',
 'iND750',
 'iNJ661',
 'iPS189',
 'iRR1083',
 'iRS1563',
 'iRS1597',
 'iSB619',
 'iSO783',
 'iYO844'}



Compunds columns
----------------
1.  id: Unique ID for the compound in the format cpdNNNNN where NNNNN is
    a five digit number (e.g. cpd00001)
2.  abbreviation: Short name of compound
3.  name: Long name of compound
4.  formula: Standard chemical format (using Hill system) in protonated
    form to match reported charge
5.  mass: Mass of compound or “null” when unknown
6.  source: Source database of compound (currently only source is
    ModelSEED)
7.  inchikey: Structure of compound using IUPAC International Chemical
    Identifier (InChI) format
8.  charge: Electric charge of compound
9.  is_core: True if compound is in core biochemistry (currently all
    compounds are set to true)
10. is_obsolete: True if compound is obsolete and replaced by different
    compound (currently all compounds are set to false)
11. linked_compound: List of compound IDs separated by semicolon related
    to this compound or “null” if not specified (used to link an
    obsolete compound to replacement compound)
12. is_cofactor: True if compound is a cofactor (currently all compounds
    are set to false)
13. deltag: Value for change in free energy of compound or “null” when
    unknown
14. deltagerr: Value for change in free energy error of compound or
    “null” when unknown
15. pka: Acid dissociation constants of compound (see below for
    description of format)
16. pkb: Base dissociation constants of compound (see below for
    description of format)
17. abstract_compound: True if compound is an abstraction of a chemical
    concept (currently all compounds are set to null)
18. comprised_of: or “null” if not specified (currently all compounds
    are set to null)
19. aliases: List of alternative names of compound separated by
    semicolon or “null” if not specified (see below for description of
    format)
20. smiles: Structure of compound using Simplified Molecular-Input
    Line-Entry System (SMILES) format
21. notes: Abbreviated notation used to store derived information about
    the compound.
"""
from collections import defaultdict, namedtuple
import numpy as np
import pandas as pd
import re
import sys

from relation_engine.biochem.kegg.parse import (
    get_kegg_reaction_ids,
    get_kegg_compound_ids,
)
from relation_engine.biochem.metacyc.parse import (
    get_metacyc_reaction_ids,
    get_metacyc_compound_ids
)
from relation_engine.biochem.ec.help import (
    ec_nums_to_edges,
    expand_internal_ec_nums,
    is_ec_num,
    norm_ec_num,
    get_ec_num_depth,
    get_ec_num_parent,
)
from relation_engine.biochem.help import (
    check_valid_key,
    log_bad_ids,
)
from src.utils.debug import dprint

MODELSEED_REACTIONS_FP = "data/modelseed/reactions.tsv"
MODELSEED_COMPOUNDS_FP = "data/modelseed/compounds.tsv"

KEGG_RXN_IDS = get_kegg_reaction_ids()
KEGG_CPD_IDS = get_kegg_compound_ids()
METACYC_RXN_IDS = get_metacyc_reaction_ids()
METACYC_CPD_IDS = get_metacyc_compound_ids()

# For checking if xref exists
RXN_IDS = {
    "KEGG": KEGG_RXN_IDS,
    "MetaCyc": METACYC_RXN_IDS
}
CPD_IDS = {
    "KEGG": KEGG_CPD_IDS,
    "MetaCyc": METACYC_CPD_IDS
}


###############################################################################
def _split_xref_strcat(xref_strcat, xref_dlm=";"):
    """
    TODO escaped delimiters?

    :param xref_str:    See entire input example
    :param xref_dlm:    See input example, defaults to ";"
    :return:            See output example

Parsing out the rows with single namespace xrefs
------------------------------------------------
* INPUT: '''cpd00001;cpd00009;cpd00012;cpd00067'''
* OUTPUT: ["cpd00001", "cpd00009", "cpd00012", "cpd00067"]
    """
    return [
        tok.strip()
        for tok in xref_strcat.split(xref_dlm)
        if tok.strip()
    ]


###############################################################################
def _split_multi_ns_xref_strcat(multi_ns_xref_strcat, multi_ns_xref_dlm="|", ns_xref_dlm=":"):
    """
    TODO escaped delimiters? no "kb|"

    :param ns_xref_str_cat: See entire example input
    :param ns_xref_dlm:     See example input, defaults to "|"
    :param ns_dlm:          See example input, defaults to ":"
    :return:                See example output

Parsing out the rows with multiple namespace xrefs
---------------------------------------------------
* INPUT: '''AraCyc: INORGPYROPHOSPHAT-RXN|BiGG: IPP1; PPA; PPA_1; PPAm|BrachyCyc: INORGPYROPHOSPHAT-RXN|KEGG: R00004|MetaCyc: INORGPYROPHOSPHAT-RXN|Name: Diphosphate phosphohydrolase; Inorganic diphosphatase; Inorganic pyrophosphatase; Pyrophosphate phosphohydrolase; diphosphate phosphohydrolase; inorganic diphosphatase; inorganic diphosphatase (one proton translocation); inorganicdiphosphatase; pyrophosphate phosphohydrolase'''
* OUTPUT: {
    "AraCyc": ["INORGPYROPHOSPHAT-RXN"],
    "BiGG": ["IPP1", "PPA", "PPA_1", "PPAm"],
    "BrachyCyc": ["INORGPYROPHOSPHAT-RXN"],
    "KEGG": ["R00004"].
    "MetaCyc": ["INORGPYROPHOSPHAT-RXN"],
    "Name": ["Diphosphate phosphohydrolase", "Inorganic diphosphatase", "Inorganic pyrophosphatase", "Pyrophosphate phosphohydrolase", "diphosphate phosphohydrolase", "inorganic diphosphatase", "inorganic diphosphatase (one proton translocation)", "inorganicdiphosphatase", "pyrophosphate phosphohydrolase"]

* WARNING:
Could have something like:
'''Name: Hexadecanoyl-CoA; Palmitoyl-CoA; Palmitoyl-CoA (n-C16:0CoA); hexadecanoyl CoA; palmitoyl CoA; palmitoyl coenzyme A; palmitoyl-CoA; palmityl-CoA'''
Note: there is a ':' in the values
}
    """
    multi_ns_xref_lis_dic = {}  # Dict of ns -> xref lists
    for ns_xref_str in multi_ns_xref_strcat.split(multi_ns_xref_dlm):
        ns, xref_strcat = ns_xref_str.split(ns_xref_dlm, 1)
        ns = ns.strip()
        xref_lis = _split_xref_strcat(xref_strcat)
        multi_ns_xref_lis_dic[ns] = xref_lis

    return multi_ns_xref_lis_dic


###############################################################################
def get_model_seed_ec_number_ids(fp=MODELSEED_REACTIONS_FP):
    gen_rxn_doc = gen_model_seed_reactions(fp=fp)
    
    ec_num_leaves = set()
    for doc in gen_rxn_doc:
        ec_num_leaves.update(doc["ec_numbers"])

    # Sanity check on leaf EC numbers
    ec_num_bads = set()
    for ec_num in ec_num_leaves:
        if not is_ec_num(ec_num):  # TODO write bad EC numbers to file
            ec_num_bads.add(ec_num)
            continue
        assert ec_num == norm_ec_num(ec_num)

    # Deal with bad ids
    log_bad_ids("ModelSEED_ec_num_bad.txt", sorted(list(ec_num_bads)))
    ec_num_leaves = ec_num_leaves - ec_num_bads

    return sorted(list(ec_num_leaves))


###############################################################################
def get_model_seed_edge_ids(fp=MODELSEED_REACTIONS_FP):
    return ec_nums_to_edges(
        get_model_seed_ec_number_ids(fp=fp)
    )


###################################################################################################
###################################################################################################
def _gen_rxn_member_types(stoich_strs: str):
    REACTANT = "reactant"
    PRODUCT = "product"
    TRANSPORT_IN = "transported_in"
    TRANSPORT_OUT = "transported_out"
    

    class Compound:

        def __init__(self, cpd_str):
            """Parse out compound information and do basic checks/normalization
            
            Parameters
            ----------
            :cpd_str:   compound string, parsed from ModelSEED stoichiometry string

            """
            # just keep compound coefficient, id, and compartment index
            self.coeff, self.cpd, self.compind = cpd_str.split(":")[:3]

            self.coeff = float(self.coeff)
            self.compind = int(self.compind)

            # Sanity check
            # Coefficient should be non-zero
            assert abs(self.coeff) > 0, f"Zero coeff {self.coeff} in compund {cpd_str}"

            # Catch slightly off zeros
            self.coeff = round(self.coeff, 8)
            
    
    class Stoichiometry:

        def __init__(self, num, stoich_str):
            """Parse out stoichiometry string, instantiate member compounds,
            and compute information for member compounds
            
            Parameters
            ----------
            :num:           index in ModelSEED database
            :stoich_str:    stoichiometry string

            """
            self.num = num
            self.stoich_str = stoich_str

            self.cpds = [Compound(cpd_str) for cpd_str in stoich_str.strip().split(";")]
            self.cpds = [cpd for cpd in self.cpds if cpd.coeff != 0]  # filter out machine precision error zeros

            # Collect information for each cpd
            self.cpd_2_info = defaultdict(lambda: ([], [], []))  # coeff(s), compind(s), rxnmemtype(s)
            for cpd in self.cpds:
                self.cpd_2_info[cpd.cpd][0].append(cpd.coeff)
                self.cpd_2_info[cpd.cpd][1].append(cpd.compind)

            # Sanity/assumption checks
            for cpd, (coeffs, compinds, _) in self.cpd_2_info.items():
                assert len(coeffs) == len(compinds)
                assert len(coeffs) in [1, 2]
                if len(coeffs) == 2:
                    assert compinds[0] != compinds[1]
                    assert coeffs[0] < 0 and coeffs[1] > 0  # neg then pos, TODO future proof?
                    if -coeffs[0] == coeffs[1]:  # if equally present on both sides eq, should be transport
                        # assert compinds in [[0, 1], [1, 0]], f"{self.num}: {self.cpd_2_coeffs_compinds}"
                        pass  # TODO what is compartment index 2?

            # Compute each cpd's reaction member type
            for cpd, (coeffs, compinds, rxnmemtypes) in self.cpd_2_info.items():
                
                # Cpd occurs on one side of eq
                if len(coeffs) == 1:
                    if coeffs[0] < 0:
                        rxnmemtypes.append(REACTANT)
                    elif coeffs[0] > 0:
                        rxnmemtypes.append(PRODUCT)
                    else:
                        raise Exception()

                # Cpd occurs on both sides of eq
                elif len(coeffs) == 2:
                    # Imbalanced on either side of eq
                    # TODO does this make sense
                    if -coeffs[0] != coeffs[1]:
                        if abs(coeffs[0]) > abs(coeffs[1]):
                            rxnmemtypes.append(REACTANT)
                        elif abs(coeffs[0]) < abs(coeffs[1]):
                            rxnmemtypes.append(PRODUCT)

                    if compinds == [0, 1]:
                        rxnmemtypes.append(TRANSPORT_OUT)
                    elif compinds == [1, 0]:
                        rxnmemtypes.append(TRANSPORT_IN)

                else:
                    raise Exception()

        @classmethod
        def parse_stoich_strs(cls, stoich_strs):
            """Factory method to instantiate all stoichiometry strings
            
            Parameters
            ----------
            :stoich_strs:   stoichiometry strings from ModelSEED database
            """
            cls.stoichs = [
                cls(i, stoich_str) if stoich_str is not None else None
                for i, stoich_str in enumerate(stoich_strs)
            ]

        @classmethod
        def gen_rxn_member_types(cls):
            for stoich in cls.stoichs:
                if stoich is None:
                    yield None
                else:
                    yield {
                        cpd: info[2]
                        for cpd, info in stoich.cpd_2_info.items()
                    }

        # @classmethod
        # def _get_repeat_cpds(cls):
        #     all_repeats = []
        #     for stoich in cls.stoichs:
        #         if stoich is None:
        #             continue
                
        #         repeats = {
        #             cpd: (coeffs, compinds)
        #             for cpd, (coeffs, compinds, _) in stoich.cpd_2_info.items()
        #             if len(coeffs) > 1
        #         }
        #         if repeats:
        #             all_repeats.append((stoich.num, repeats))

        #     return all_repeats

    Stoichiometry.parse_stoich_strs(stoich_strs)
    return Stoichiometry.gen_rxn_member_types()



########################################################################################################################
########################################################################################################################
def gen_model_seed_reactions(fp):
    """Generate ModelSEED reaction vertex documents

    :param fp:  Filepath to ModelSEED reactions data file.
                Should be retrieved from
                https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv
    """
    # Read TSV and replace NaNs with None
    # Since NaNs aren't actually Falsey and are otherwise difficult
    # TODO replacement changes every datum to type object?
    df = pd.read_csv(fp, sep="\t").replace({np.nan: None})

    columns = df.columns.tolist()
    columns_2_ind = dict(zip(columns, range(len(columns))))

    ## xref or ref, really ##

    # Example multi ref: '''AraCyc: INORGPYROPHOSPHAT-RXN|BiGG: IPP1; PPA; PPA_1; PPAm|BrachyCyc: INORGPYROPHOSPHAT-RXN'''
    multi_ns_xref_keys = ["pathways", "aliases"]
    # Example single ref: '''cpd00001;cpd00009;cpd00012;cpd00067'''
    single_ns_xref_keys = ["ec_numbers", "compound_ids", "linked_reaction"]

    for row in df.iterrows():
        _, rowdat = row[0], row[1].tolist()

        # Parse out the rows with multiple namespace xrefs
        for k in multi_ns_xref_keys:
            multi_ns_xref_strcat = rowdat[columns_2_ind[k]]  # Either None or str
            rowdat[columns_2_ind[k]] = (
                _split_multi_ns_xref_strcat(multi_ns_xref_strcat)
                if multi_ns_xref_strcat
                else {}
            )

        # Parse out the rows with single namespace xrefs
        for k in single_ns_xref_keys:
            single_ns_xref_strcat = rowdat[columns_2_ind[k]]  # Either None or str
            rowdat[columns_2_ind[k]] = (
                _split_xref_strcat(single_ns_xref_strcat, xref_dlm=("|" if k == "ec_numbers" else ";"))
                if single_ns_xref_strcat
                else []
            )

        doc = dict(zip(columns, rowdat))
        yield doc


########################################################################################################################
########################################################################################################################
def gen_model_seed_reaction_xrefs(fp):
    """
    Currently just do doc["aliases"] and doc["ec_numbers"]
    Exclude intra-ModelSEED refs
    """
    bad_rxn_xrefs = set()

    for doc in gen_model_seed_reactions(fp):
        for ns, xrefs in doc["aliases"].items():
            if ns not in ["KEGG", "MetaCyc", "RHEA"]:
                continue

            for xref in xrefs:
                
                # Some xrefs are old and deleted
                if xref not in RXN_IDS[ns]:
                    bad_rxn_xrefs.add((ns, xref))
                    continue

                yield {
                    "id": f"{doc['id']}@{ns}_reaction@{xref}",
                    "xref_coll": f"{ns}_reaction",
                    "is_alias": 1,
                    # Will have coll name parsed out (from/to)
                    "from": f"ModelSEED_reaction/{doc['id']}",
                    "to": f"{ns}_reaction/{xref}",
                    # Will be popped
                    "_collection": "ModelSEED_reaction_xref",
                    "_is_xref": 1,
                }

        for xref in doc["ec_numbers"]:

            if not is_ec_num(xref):
                bad_rxn_xrefs.add(("EC", xref))
                continue
            
            xref = norm_ec_num(xref)

            yield {
                "id": f"{doc['id']}@EC_number@{xref}",
                "xref_coll": "EC_number",
                "is_alias": 0,
                # Will have coll name parsed out (from/to)
                "from": f"ModelSEED_reaction/{doc['id']}",
                "to": f"EC_number/{xref}",
                # Will be popped
                "_collection": "ModelSEED_reaction_xref",
                "_is_xref": 1,
            }

    log_bad_ids("ModelSEED_reaction_xref_bad_ids.txt", sorted(list(bad_rxn_xrefs)))


###################################################################################################
###################################################################################################
def gen_model_seed_ec_numbers(fp=MODELSEED_REACTIONS_FP):
    ms_ec_nums = get_model_seed_ec_number_ids(fp=fp)

    # Yield MS EC numbers
    for ec_num in ms_ec_nums:
        yield {
            "id": ec_num,
            # Will be either KEGG, ModelSEED, or null (for internal nodes)
            "source": "ModelSEED",
            # Will be popped
            "_collection": "EC_number",
        }

    # Yield any internal nodes
    for ec_num in expand_internal_ec_nums(ms_ec_nums, return_new=True):
        yield {
            "id": ec_num,
            # Will be either KEGG, ModelSEED, or null (for internal nodes)
            "source": None,
            # Will be popped
            "_collection": "EC_number",
        }


###################################################################################################
###################################################################################################
def gen_model_seed_ec_edges(fp=MODELSEED_REACTIONS_FP):
    for ec_child, ec_parent in get_model_seed_edge_ids(fp=fp):

        yield {
            "id": f"{ec_child}@{ec_parent}",
            "from": ec_child,
            "to": ec_parent,
            # Will be popped
            "_collection": "EC_edge",
        }


###################################################################################################
###################################################################################################
def gen_model_seed_compounds(fp):
    df = pd.read_csv(fp, sep="\t").replace({np.nan: None})

    columns = df.columns.tolist()
    columns_2_ind = dict(zip(columns, range(len(columns))))

    multi_ns_xref_keys = ["aliases"]
    single_ns_xref_keys = ["linked_compound", "pka", "pkb"]

    for row in df.iterrows():
        _, rowdat = row[0], row[1].tolist()

        # Parse out the rows with multiple namespace xrefs
        for k in multi_ns_xref_keys:
            multi_ns_xref_strcat = rowdat[columns_2_ind[k]]  # Either None or str
            rowdat[columns_2_ind[k]] = (
                _split_multi_ns_xref_strcat(multi_ns_xref_strcat)
                if multi_ns_xref_strcat
                else {}
            )

        # Parse out the rows with single namespace xrefs
        for k in single_ns_xref_keys:
            single_ns_xref_strcat = rowdat[columns_2_ind[k]]  # Either None or str
            rowdat[columns_2_ind[k]] = (
                _split_xref_strcat(single_ns_xref_strcat)
                if single_ns_xref_strcat
                else []
            )

        doc = dict(zip(columns, rowdat))
        yield doc


########################################################################################################################
########################################################################################################################
def gen_model_seed_compound_xrefs(fp):
    """
    Currently just do doc["aliases"]
    Exclude intra-ModelSEED refs
    """
    bad_cpd_xrefs = set()

    for doc in gen_model_seed_compounds(fp):
        for ns, xrefs in doc["aliases"].items():
            if ns not in ["KEGG", "MetaCyc", "RHEA"]:
                continue

            for xref in xrefs:
                
                # hack?
                if xref not in CPD_IDS[ns]:
                    bad_cpd_xrefs.add((ns, xref))
                    continue

                # id_ = f"{doc['id']}@{ns}_compound@{xref}"

                # try:
                #     check_valid_key(id_)
                # except Exception as e:
                #     dprint(id_, e, run=None, print_kw={"file": sys.stderr})
                #     continue

                yield {
                    "id": f"{doc['id']}@{ns}_compound@{xref}",
                    "xref_coll": f"{ns}_compound",
                    "is_alias": 1,
                    # Will have the coll name parsed out (from/to)
                    "from": f"ModelSEED_compound/{doc['id']}",
                    "to": f"{ns}_compound/{xref}",
                    # Will be popped
                    "_collection": "ModelSEED_compound_xref",
                    "_is_xref": 1,
                }

    log_bad_ids("ModelSEED_compound_xref_bad_ids.txt", sorted(list(bad_cpd_xrefs)))


###################################################################################################
###################################################################################################
def gen_model_seed_reaction_to_compound(fp=MODELSEED_REACTIONS_FP):
    """Generates rxn->cpd relationships by contents of "compound_ids" field
    rather than any equation field like "stoichiometry"
    """
    df_rxn = pd.read_csv(fp, sep="\t").replace({np.nan: None})
    rxn_2_cpds = {
        x: (y.split(";") if y is not None else None)
        for x, y in zip(df_rxn["id"], df_rxn["compound_ids"].tolist())
    }
    gen_rxnmemtypes = _gen_rxn_member_types(df_rxn["stoichiometry"].tolist())

    for (rxn, cpds), rxnmemtypes in zip(rxn_2_cpds.items(), gen_rxnmemtypes):
        
        # TODO related compounds (cpds) might not match what's in the stoichiometry (rxnmemtypes)?
        if cpds is None:
            continue

        for cpd in cpds:

            yield {
                "id": f"{rxn}@{cpd}",
                "rxn_member_type": rxnmemtypes.get(cpd),
                # Will have the coll name parsed out
                "from": f"ModelSEED_reaction/{rxn}",
                "to": f"ModelSEED_compound/{cpd}",
                # Will be popped
                "_collection": "ModelSEED_reaction_to_compound",
                "_is_xref": 1,
            }

    # Sanity check
    try:
        next(gen_rxnmemtypes)
    except StopIteration:
        pass
    else:
        assert False


###################################################################################################
###################################################################################################
def gen_model_seed_reaction_merges(fp):
    df = pd.read_csv(fp, sep="\t").replace({np.nan: None})
    rxn_2_rxns_dic = {
        x: y.split(";")
        for x, y in zip(df["id"].tolist(), df["linked_reaction"].tolist())
        if y
    }

    rxn_2_rxn_lis = []

    for rxn0, rxns in rxn_2_rxns_dic.items():
        for rxn1 in rxns:
            pair = (rxn1, rxn0)  # rxn1 merged into rxn0
            assert pair not in rxn_2_rxn_lis  # sanity check: merge is one way
            rxn_2_rxn_lis.append(pair)

    for pair in rxn_2_rxn_lis:
        yield {
            "id": f"{pair[0]}/{pair[1]}",
            # Will have coll name parsed out
            "from": f"ModelSEED_reaction/{pair[0]}",
            "to": f"ModelSEED_reaction/{pair[1]}",
            # Will be popped
            "_collection": "ModelSeed_reaction_merges",
        }


########################################################################################################################
########################################################################################################################
def gen_model_seed_compound_merges(fp):
    df = pd.read_csv(fp, sep="\t").replace({np.nan: None})
    cpd_2_cpds_dic = {
        x: y.split(";")
        for x, y in zip(df["id"].tolist(), df["linked_compound"].tolist())
        if y
    }

    cpd_2_cpd_lis = []

    for cpd0, cpds in cpd_2_cpds_dic.items():
        for cpd1 in cpds:
            pair = (cpd1, cpd0)  # cpd1 merged into cpd0
            assert pair not in cpd_2_cpd_lis  # sanity check: merge is one way
            cpd_2_cpd_lis.append(pair)

    for pair in cpd_2_cpd_lis:
        yield {
            "id": f"{pair[0]}/{pair[1]}",
            # Will have coll name parsed out
            "from": f"ModelSEED_compound/{pair[0]}",
            "to": f"ModelSEED_compound/{pair[1]}",
            # Will be popped
            "_collection": "ModelSEED_compound_merges",
        }
