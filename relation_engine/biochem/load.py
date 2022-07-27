from collections import namedtuple
from datetime import datetime
from itertools import chain
import os
import time

from arango import ArangoClient

from relation_engine.batchload.delta_load import load_graph_delta, set_verbosity
from relation_engine.batchload.time_travelling_database import (
    ArangoBatchTimeTravellingDB
)
from relation_engine.biochem.kegg.parse import (
    gen_kegg_reaction_to_orthology,
    gen_kegg_reactions,
    gen_kegg_compounds,
    gen_kegg_orthology,
    gen_kegg_ec_numbers,
    gen_kegg_ec_edges,
    gen_kegg_enzyme_to_orthology,
)
from relation_engine.biochem.metacyc.parse import (
    gen_metacyc_reactions,
    gen_metacyc_compounds,
)
from relation_engine.biochem.modelseed.parse import (
    gen_model_seed_ec_numbers,
    gen_model_seed_ec_edges,
    gen_model_seed_reactions,
    gen_model_seed_reaction_xrefs,
    gen_model_seed_compounds,
    gen_model_seed_compound_xrefs,
    gen_model_seed_reaction_to_compound,
    gen_model_seed_reaction_merges,
    gen_model_seed_compound_merges,
)
from relation_engine.biochem.rhea.parse import (
    gen_chebi_terms,
    gen_rhea_reactions,
)
from relation_engine.biochem.sso.parse import (
    gen_sso_terms,
    gen_sso_to_model_seed_reaction,
)
from relation_engine.biochem.help import (
    gen_doc_diff,
)
from src.utils.debug import dprint


CHEBI_VERSION = ""
KEGG_VERSION = "102.0"
METACYC_VERSION = "26.0"
MODELSEED_VERSION = "194ac8afe48f8a606c0dd07ba3c7af10c02ba2fd"
RHEA_VERSION = ""
SSO_VERSION = "2020-04-17"

MODELSEED_REACTIONS_FP = "data/modelseed/reactions.tsv"
MODELSEED_COMPOUNDS_FP = "data/modelseed/compounds.tsv"
KEGG_REACTIONS_FP = "data/kegg/reaction.tsv"
KEGG_COMPOUNDS_FP = "data/kegg/compound.tsv"
KEGG_REACTION_FULL_FP = "data/kegg/reaction_full.txt"
KEGG_ORTHOLOGY_FULL_FP = "data/kegg/ko_full.txt"
KEGG_ENZYME_FULL_FP = "data/kegg/enzyme_full.txt"
METACYC_REACTIONS_FP = "data/metacyc/26.0/data/reactions.dat"
METACYC_COMPOUNDS_FP = "data/metacyc/26.0/data/compounds.dat"
CHEBI_ID_FP = "data/rhea/tsv/chebiId_name.tsv"
RHEA_REACTIONS_FP = "data/rhea/tsv/rhea-directions.tsv"
SSO_TERM_FP = "data/sso/SSO_dictionary.json"
SSO_REACTION_FP = "data/sso/SSO_reactions.json"

ARANGO_URL = "http://localhost:8531"
ARANGO_DB = "sumin_test"
ARANGO_USER_FILE = "tmp/username"
ARANGO_PASS_FILE = "tmp/password"

LOAD_NAMESPACE = "biochem"
LOAD_REGISTRY_COLL_NAME = "delta_load_registry"


def get_timestamp(regress=False):
    """Regress for fake release timestamp, 100 days back"""
    ts = time.time() * 1e6  # ms
    if regress:
        ts -= 100 * 24 * 3600 * 1e6
    return int(ts)


def get_load_version(ver=""):
    if ver:
        ver += "@"
    ver += datetime.today().strftime("%Y-%m-%d@%H:%M:%S.%f")
    return ver


set_verbosity(True)  # for delta loader function


client = ArangoClient(hosts=ARANGO_URL)
with open(ARANGO_USER_FILE) as fh:
    user = fh.read().strip()
with open(ARANGO_PASS_FILE) as fh:
    pswd = fh.read().strip()
db = client.db(ARANGO_DB, username=user, password=pswd)


def clear_collections():
    dprint("Clearing collections", run=None)

    coll_name_lis = [
        "KEGG_compound",
        "KEGG_reaction",
        "MetaCyc_compound",
        "MetaCyc_reaction",
        "EC_number",
        "EC_edge",
        "ModelSEED_compound",
        "ModelSEED_compound_merge",
        "ModelSEED_compound_xref",
        "ModelSEED_reaction",
        "ModelSEED_reaction_merge",
        "ModelSEED_reaction_to_compound",
        "ModelSEED_reaction_xref",
    ]

    for coll_name in coll_name_lis:
        coll = db.collection(coll_name)
        coll.truncate()


# clear_collections()
# import sys; sys.exit()

VertexLoadCohort = namedtuple(
    "VertexLoadCohort",
    [
        "vertex_coll_name",
        "vertex_coll_name_lis",
        "default_edge_coll_name",
        "edge_coll_name_lis",
        "merge_coll_name",
        "iter_vertex",
        "iter_edge",
        "iter_merge",
    ]
)

vertex_load_cohort_lis = [
    VertexLoadCohort("KEGG_orthology", None, None, None, None, gen_kegg_orthology(KEGG_ORTHOLOGY_FULL_FP), None, None),
    VertexLoadCohort("KEGG_compound", None, None, None, None, gen_kegg_compounds(KEGG_COMPOUNDS_FP), None, None),
    VertexLoadCohort(
        vertex_coll_name="KEGG_reaction",
        vertex_coll_name_lis=["KEGG_orthology"],
        default_edge_coll_name=None,
        edge_coll_name_lis=["KEGG_reaction_xref"],
        merge_coll_name=None,
        iter_vertex=gen_kegg_reactions(KEGG_REACTIONS_FP),
        iter_edge=gen_kegg_reaction_to_orthology(KEGG_REACTION_FULL_FP),
        iter_merge=None,
    ),
    VertexLoadCohort("MetaCyc_compound", None, None, None, None, gen_metacyc_compounds(METACYC_COMPOUNDS_FP), None, None),
    VertexLoadCohort("MetaCyc_reaction", None, None, None, None, gen_metacyc_reactions(METACYC_REACTIONS_FP), None, None),
    VertexLoadCohort("ChEBI_term", None, None, None, None, gen_chebi_terms(CHEBI_ID_FP), None, None),
    VertexLoadCohort("Rhea_reaction", None, None, None, None, gen_rhea_reactions(RHEA_REACTIONS_FP), None, None),
    VertexLoadCohort(
        vertex_coll_name="EC_number",
        vertex_coll_name_lis=["KEGG_orthology"],
        default_edge_coll_name=None,
        edge_coll_name_lis=["EC_edge", "EC_number_xref"],
        merge_coll_name=None,
        iter_vertex=chain(
            gen_kegg_ec_numbers(KEGG_ENZYME_FULL_FP),  # do KEGG EC numbers first
            gen_doc_diff(  # then do ModelSEED EC numbers
                gen_model_seed_ec_numbers(MODELSEED_REACTIONS_FP),
                gen_kegg_ec_numbers(KEGG_ENZYME_FULL_FP)
            ),
        ),
        iter_edge=chain(
            gen_kegg_ec_edges(KEGG_ENZYME_FULL_FP),  # do KEGG EC edges first
            gen_doc_diff(  # then do ModelSEED EC edges
                gen_model_seed_ec_edges(MODELSEED_REACTIONS_FP),
                gen_kegg_ec_edges(KEGG_ENZYME_FULL_FP)
            ),
            gen_kegg_enzyme_to_orthology(KEGG_ENZYME_FULL_FP),
        ),    
        iter_merge=None,
    ),
    VertexLoadCohort(
        vertex_coll_name="ModelSEED_compound",
        vertex_coll_name_lis=["KEGG_compound", "MetaCyc_compound", "EC_number"],
        default_edge_coll_name=None,
        edge_coll_name_lis=["ModelSEED_compound_xref"],
        merge_coll_name="ModelSEED_compound_merge",
        iter_vertex=gen_model_seed_compounds(MODELSEED_COMPOUNDS_FP),
        iter_edge=gen_model_seed_compound_xrefs(MODELSEED_COMPOUNDS_FP),
        iter_merge=gen_model_seed_compound_merges(MODELSEED_COMPOUNDS_FP)
    ),
    VertexLoadCohort(
        vertex_coll_name="ModelSEED_reaction",
        vertex_coll_name_lis=["ModelSEED_compound", "KEGG_reaction", "MetaCyc_reaction", "EC_number"],
        default_edge_coll_name=None,
        edge_coll_name_lis=["ModelSEED_reaction_to_compound", "ModelSEED_reaction_xref"],
        merge_coll_name="ModelSEED_reaction_merge",
        iter_vertex=gen_model_seed_reactions(MODELSEED_REACTIONS_FP),
        iter_edge=chain(
            gen_model_seed_reaction_to_compound(MODELSEED_REACTIONS_FP),
            gen_model_seed_reaction_xrefs(MODELSEED_REACTIONS_FP)
        ),
        iter_merge=gen_model_seed_reaction_merges(MODELSEED_REACTIONS_FP)
    ),
    VertexLoadCohort(
        vertex_coll_name="SSO_term",
        vertex_coll_name_lis=["ModelSEED_reaction"],
        default_edge_coll_name=None,
        edge_coll_name_lis=["SSO_edge", "SSO_xref"],
        merge_coll_name=None,
        iter_vertex=gen_sso_terms(SSO_TERM_FP),
        iter_edge=gen_sso_to_model_seed_reaction(SSO_REACTION_FP),
        iter_merge=None,
    )
]


for cohort in vertex_load_cohort_lis[9:]:
    attdb = ArangoBatchTimeTravellingDB(
        db,
        LOAD_REGISTRY_COLL_NAME,
        cohort.vertex_coll_name,
        default_edge_collection=cohort.default_edge_coll_name,
        edge_collections=cohort.edge_coll_name_lis,
        merge_collection=cohort.merge_coll_name,
        vertex_collections=cohort.vertex_coll_name_lis,
    )

    dprint(f"Begin load_graph_delta for vertex collection {cohort.vertex_coll_name}", run=None)

    load_graph_delta(
        LOAD_REGISTRY_COLL_NAME,
        cohort.iter_vertex,
        attdb,
        get_timestamp(),
        get_timestamp(),
        get_load_version(),
        edge_source=cohort.iter_edge,
        merge_source=cohort.iter_merge,
    )









# TODO option to mark as full load or update load (don't delete nodes without the last_version)
# TODO QA on uploaded network?