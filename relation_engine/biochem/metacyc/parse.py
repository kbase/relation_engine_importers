METACYC_REACTIONS_FP = "data/metacyc/26.0/data/reactions.dat"
METACYC_COMPOUNDS_FP = "data/metacyc/26.0/data/compounds.dat"


def get_metacyc_reaction_ids(fp=METACYC_REACTIONS_FP):
    rxn_ids = list(gen_metacyc_reactions(fp))
    rxn_ids = [d["id"] for d in rxn_ids]
    return rxn_ids


def get_metacyc_compound_ids(fp=METACYC_COMPOUNDS_FP):
    cpd_ids = list(gen_metacyc_compounds(fp))
    cpd_ids = [d["id"] for d in cpd_ids]
    return cpd_ids


########################################################################################################################
########################################################################################################################
def gen_metacyc_reactions(fp):
    prefix = "UNIQUE-ID - "

    with open(fp, encoding="ISO-8859-1") as fh:
        for line in fh:
            if line.startswith("UNIQUE-ID"):
                assert line.startswith(prefix)
                rxn_id = line[len(prefix):].strip()
                yield {
                    "id": rxn_id
                }


########################################################################################################################
########################################################################################################################
def gen_metacyc_compounds(fp):
    prefix = "UNIQUE-ID - "

    with open(fp, encoding="ascii", errors="surrogateescape") as fh:
        for line in fh:
            if line.startswith("UNIQUE-ID"):
                assert line.startswith(prefix)
                cpd_id = line[len(prefix):].strip()
                yield {
                    "id": cpd_id
                }
