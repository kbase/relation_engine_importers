import json
import re


SSO_TERM_FP = "data/sso/SSO_dictionary.json"
SSO_REACTION_FP = "data/sso/SSO_reactions.json"




###############################################################################
def get_sso_ids(fp=SSO_TERM_FP):
    with open(fp) as fh:
        sso = json.load(fh)["term_hash"]

    return list(sso.keys())


########################################################################################################################
########################################################################################################################
def gen_sso_terms(fp=SSO_TERM_FP):
    with open(fp) as fh:
        sso = json.load(fh)["term_hash"]

    # Sanity check
    for k, v in sso.items():
        assert isinstance(k, str)
        assert re.match(r"SSO:\d{9}$", k)
        assert sorted(list(v.keys())) == ["id", "name"]
        assert isinstance(v["id"], str)
        assert isinstance(v["name"], str)
        assert k == v["id"]

    # Yield
    for k, v in sso.items():
        yield {
            "id": k,
            "name": v["name"],
        }


########################################################################################################################
########################################################################################################################
def gen_sso_to_model_seed_reaction(fp=SSO_REACTION_FP):
    with open(fp) as fh:
        sso_2_rxns = json.load(fh)

    # Sanity check
    # Skip ModelSEED ID verification for now (circular imports)
    sso_ids = get_sso_ids()
    for sso_id, ms_rxn_ids in sso_2_rxns.items():
        assert sso_id in sso_ids
        assert isinstance(ms_rxn_ids, list)
        assert len(ms_rxn_ids)

    # Yield
    SELF_COLL = "SSO_term"
    SELF_XREF_COLL = "SSO_xref"
    XREF_NS_COLL = "ModelSEED_reaction"
    for sso_id, ms_rxn_ids in sso_2_rxns.items():
        for ms_rxn_id in ms_rxn_ids:

            yield {
                "id": f"{sso_id}@{XREF_NS_COLL}@{ms_rxn_id}",
                "xref_coll": XREF_NS_COLL,
                # Will have coll parsed out
                "from": f"{SELF_COLL}/{sso_id}",
                "to": f"{XREF_NS_COLL}/{ms_rxn_id}",
                # Will be popped
                "_is_xref": 1,
                "_collection": SELF_XREF_COLL,
            }
        
