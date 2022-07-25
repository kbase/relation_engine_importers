"""
Contains the currently extant ranks for NCBI taxa as of 2022/07/01.
Source: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7408187/#sup1, table S3
"""

RANKS_NON_HIERARCHICAL = set([
    "clade",
    "no rank",
    # We leave out other currenly unused ranks for now to avoid more tests, possible
    # future removal of the ranks and therefore future bugginess.
    # We also leave out the unused "unclassified <name>" rank as it would require special
    # handling.
])

RANKS_SPECIES_AND_BELOW = set([
    "species",
    "forma specialis",
    "subspecies",
    "varietas",
    "morph",
    "subvariety",
    "forma",
    "serogroup",
    "pathogroup",
    "serotype",
    "biotype",
    "genotype",
    "strain",
    "isolate",
])

RANKS_ALL = set(RANKS_NON_HIERARCHICAL | RANKS_SPECIES_AND_BELOW | set([
    "superkingdom",
    "kingdom",
    "subkingdom",
    "superphylum",
    "phylum",
    "subphylum",
    "infraphylum",
    "superclass",
    "class",
    "subclass",
    "infraclass",
    "cohort",
    "subcohort",
    "superorder",
    "order",
    "suborder",
    "infraorder",
    "parvorder",
    "superfamily",
    "family",
    "subfamily",
    "tribe",
    "subtribe",
    "genus",
    "subgenus",
    "section",
    "subsection",
    "series",
    "subseries",
    "species group",
    "species subgroup",
]))
