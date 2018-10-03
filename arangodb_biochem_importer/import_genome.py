"""
Import a genome into the database from a workspace reference.
"""

import kbase_workspace_utils as ws


def import_genome(ref):
    # Unfortunately the workspace does not support streaming data
    genome_obj = ws.download_obj(ref)['data'][0]
    print(genome_obj['data'][0]['info'])
