"""
EC numbers are sourced from KEGG Enzyme and then ModelSEED
"""

import re


###############################################################################
MAX_EC_NUM_DEPTH = 4
EC_DLM = "."
EC_GAP = "-"
EC_ROOT = "Root"


#############################
def norm_ec_num(ec_num, root_ok=False):
    """Pad any hyphens in the 4 slots"""
    assert is_ec_num(ec_num, root_ok=root_ok), ec_num

    # Root
    if root_ok and ec_num == EC_ROOT:
        return ec_num

    # Non-root
    ec_num = [tok for tok in ec_num.strip().strip(EC_DLM).split(EC_DLM)]
    if len(ec_num) < MAX_EC_NUM_DEPTH:
        ec_num.extend([EC_GAP] * (MAX_EC_NUM_DEPTH - len(ec_num)))
    return EC_DLM.join(ec_num)


#############################
def get_ec_num_depth(ec_num):
    assert is_ec_num(ec_num, root_ok=False)

    ec_num = norm_ec_num(ec_num, root_ok=False)
    return len([tok for tok in ec_num.split(EC_DLM) if tok != EC_GAP])


#############################
def get_ec_num_parent(ec_num, use_root=True):
    assert is_ec_num(ec_num)
    ec_num = norm_ec_num(ec_num)

    if not ec_num.count(EC_DLM):
        return EC_ROOT if use_root else None
    parent = EC_DLM.join(ec_num.split(EC_DLM)[:-1])
    return parent


#############################
def is_ec_num(ec_num, root_ok=False):
    if root_ok and ec_num == EC_ROOT:
        return True

    assert isinstance(ec_num, str)
    assert len(ec_num) > 0

    # First: weak regex checking
    # Doesn't take fully into account the ordering of numbers, dashes, and letters
    regexes = [
        r"^((\d+|-)\.){1,3}([A-Za-z0-9]+|-)?$",  # ends in . or full
        r"^(\d+|-)(\.(\d+|-)){0,2}(\.([A-Za-z0-9]+|-))?$",  # does not end in . or full
    ]
    if not any([
        re.match(regex, ec_num)
        for regex in regexes
    ]):
        return False

    # Check that dashes come at end
    toks = [tok for tok in ec_num.split(EC_DLM) if tok]
    toksort = sorted(toks, key=lambda e: e == EC_GAP)
    if toks != toksort:
        return False

    # Check that letters only occur in 4th number
    for i, tok in enumerate(ec_num.split(EC_DLM)):
        if i < MAX_EC_NUM_DEPTH - 1:
            assert not re.search(r"[A-Za-z]", tok)
        
    return True


#############################
def ec_nums_to_edges(ec_nums):
    ec_num_edges = set()  # cache seen EC number edges

    for ec_num in ec_nums:

        # Sanity check
        assert is_ec_num(ec_num), ec_num
        assert ec_num == norm_ec_num(ec_num, root_ok=True)

        for depth in range(MAX_EC_NUM_DEPTH - 1, -1, -1):  # 3 2 1 0
            ec_num_child = EC_DLM.join(ec_num.split(EC_DLM)[:depth + 1])
            ec_num_parent = EC_DLM.join(ec_num.split(EC_DLM)[:depth]) if depth else EC_ROOT

            edge = (
                norm_ec_num(ec_num_child, root_ok=False),
                norm_ec_num(ec_num_parent, root_ok=ec_num_parent == EC_ROOT)
            )
            ec_num_edges.add(edge)

    return sorted(list(ec_num_edges))


#############################
def expand_internal_ec_nums(ec_nums, return_new=False, root_ok=True):
    """Expand set of EC numbers to include internal nodes"""
    ec_nums_original = ec_nums

    ec_nums = set(ec_nums)
    if root_ok:
        ec_nums.add(EC_ROOT)

    # Add parent EC numbers
    for ec_num in ec_nums_original:
        for depth in range(MAX_EC_NUM_DEPTH - 1, 0, -1):  # 3 2 1
            ec_num_parent = EC_DLM.join(ec_num.split(EC_DLM)[:depth])
            ec_num_parent = norm_ec_num(ec_num_parent)  # pad hyphens
            ec_nums.add(ec_num_parent)
                
    if return_new:
        return sorted(list(ec_nums - set(ec_nums_original)))
    else:
        return sorted(list(ec_nums))