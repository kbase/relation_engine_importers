

###############################################################################
def is_ec_name(name):
    if is_ec_num(name):  # if only ec num, no name
        return True
    ec_num, ec_name = re.split(r"\s", name, 1)
    return is_ec_num(ec_num)



#########
def parse_ec_tree_ec_name(name):
    name = name.replace("\\/", "/")  # get rid of escapes for forward slashes
    if is_ec_num(name):  # if only ec num, no name
        name += " "
    ec_num, ec_name = re.split(r"\s+", name, 1)
    ec_num = norm_ec_num(ec_num)

    assert is_ec_num(ec_num, exp_norm=True), name  # sanity check

    return ec_num, ec_name


#########
def parse_ec_tree_ko_name(name):
    name = name.replace("\\/", "/")  # get rid of escapes for forward slashes
    ko_id, ko_name = re.split(r"\s+", name, 1)

    assert re.match(r"^K\d{5}$", ko_id), name  # sanity check

    return {
        "id": ko_id,
        "name": ko_name,
    }



###############################################################################
def traverse_ec_tree_nodes(ec_tree):
    ec_num, ec_name = parse_ec_tree_ec_name(ec_tree["name"])
    depth = get_ec_num_depth(ec_num)
    has_children = "children" in ec_tree
    has_ec_children = has_children and is_ec_name(ec_tree["children"][0]["name"])
    has_ko_children = has_children and not is_ec_name(ec_tree["children"][0]["name"])

    doc = {
        "id": ec_num,
        "name": ec_name,
        "source": "KEGG",
    }

    if has_children:

        if has_ec_children:

            for ec_subtree in ec_tree["children"]:
                yield from traverse_ec_tree_nodes(ec_subtree)

        elif has_ko_children:

            doc.update({
                "ko": [
                    parse_ec_tree_ko_name(doc["name"])
                    for doc in ec_tree["children"]
                ]
            })
            
    yield doc


###############################################################################
def traverse_ec_tree_edges(ec_tree):
    parent_ec_num, _ = parse_ec_tree_ec_name(ec_tree["name"])
    parent_depth = get_ec_num_depth(parent_ec_num)
    has_children = "children" in ec_tree
    has_ec_children = has_children and is_ec_name(ec_tree["children"][0]["name"])
    has_ko_children = has_children and not is_ec_name(ec_tree["children"][0]["name"])

    if has_ec_children:
        for ec_subtree in ec_tree["children"]:
            child_ec_num, _ = parse_ec_tree_ec_name(ec_subtree["name"])
            
            yield {
                "id": f"{child_ec_num}@{parent_ec_num}",
                "from": f"{child_ec_num}",
                "to": f"{parent_ec_num}",
                # Will be popped
                "_collection": "EC_edge"
            }

            yield from traverse_ec_tree_edges(ec_subtree)


###################################################################################################
###################################################################################################
def gen_kegg_ec_numbers(fp_ec_tree):
    with open(fp_ec_tree) as fh:
        ec_tree = json.load(fh)

    ec_tree["name"] = " Root"  # don't know why root is just "ko01000"

    return traverse_ec_tree_nodes(ec_tree)



###################################################################################################
###################################################################################################
def gen_kegg_ec_edges(fp_ec_tree):
    with open(fp_ec_tree) as fh:
        ec_tree = json.load(fh)

    ec_tree["name"] = " Root"  # don't know why root is just "ko01000"

    return traverse_ec_tree_edges(ec_tree)




###################
def build_kegg_model_seed_ec_tree(fp=KEGG_ENZYME_FULL_FP):
    """Do this to get edges"""
    ec_nums = get_kegg_leaf_ec_number_ids(fp)
    ec_nums = sorted(list(set(ec_nums)))

    ec_tree = {
        EC_ROOT: {}
    }
    
    for ec_num in ec_nums:
        assert ec_num == norm_ec_num(ec_num)
        assert get_ec_num_depth(ec_num) == MAX_EC_NUM_DEPTH

        ec_subtree = ec_tree[EC_ROOT]
        for i, tok in enumerate(ec_num.split(EC_DLM)):  # 0.1.2.3
            try:
                tok = int(tok)
            except ValueError:
                pass
            
            if i <= 1:
                if tok not in ec_subtree:
                    ec_subtree[tok] = {}

                ec_subtree = ec_subtree[tok]

            elif i == 2:
                if tok not in ec_subtree:
                    ec_subtree[tok] = []  # not really tree ...
                
                ec_subtree = ec_subtree[tok]

            elif i == 3:
                if tok not in ec_subtree:
                    ec_subtree.append(tok)

            else:
                raise Exception()

    return ec_tree


###################
def traverse_gen_ec_tree(ec_tree):
    """Yield edges from current node to any children nodes"""

    for parent_num, ec_subtree in ec_tree.items():
        if isinstance(ec_subtree, dict):
            for child_num in ec_subtree.keys():
                yield {
                    "id": f"{child_num}@{parent_num}",
                    "from": child_num,
                    "to": parent_num,
                    # Will be popped
                    "_collection": "EC_edge",
                }

            yield from traverse_gen_ec_tree(ec_subtree)

        elif isinstance(ec_subtree, list):
            for child_num in ec_subtree:
                yield {
                    "id": f"{child_num}@{parent_num}",
                    "from": child_num,
                    "to": parent_num,
                    # Will be popped
                    "_collection": "EC_edge",
                }

        else:
            raise Exception()
