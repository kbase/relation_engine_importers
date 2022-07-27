from collections import defaultdict
import json
import numpy as np
import os
import pandas as pd
import re
import sys

from src.utils.debug import dprint


###############################################################################
LOG_DIR = "tmp/log"
ERR_DIR = os.path.join(LOG_DIR, "err")  # write rejected IDs
os.makedirs(ERR_DIR, exist_ok=True)


####################
def log_bad_ids(fn, ids):
    fp  = os.path.join(ERR_DIR, fn)
    with open(fp, "w") as fh:
        json.dump(ids, fh, indent=4)


###############################################################################
def check_valid_key(k):
    """Check that it is a valid ArangoDB key"""
    if not isinstance(k, str):
        raise ValueError(f"Key {k} is not str")
    num_bytes = len(k.encode("utf-8"))
    if num_bytes < 1 or 254 > num_bytes:
        raise ValueError(f"Key {k} has wrong num bytes {num_bytes}")
    allowed_chars = "[A-Za-z0-9_\-:.@()+,=;$!*'%]"
    for c in k:
        if c not in allowed_chars:
            raise ValueError(f"Key {k} has disallowed char {c}")


###############################################################################
def gen_line(fp):
    with open(fp) as fh:
        for line in fh:
            yield line


###############################################################################
def gen_doc_diff(doc_iter_from, doc_iter_exclude):
    """Gen from doc_iter_from unless it's contained in doc_iter_exclude"""
    ids1 = [doc["id"] for doc in doc_iter_exclude]

    for doc in doc_iter_from:
        if doc["id"] not in ids1:
            yield doc

