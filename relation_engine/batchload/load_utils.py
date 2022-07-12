"""
Utilities for loading graph data into the relation engine.
"""


# since this is KBase internal code we can be a bit less compassionate re good
# error messages, e.g. throwing KeyErrors or TypeErrors vs a more descriptive message.
# As a result we get slightly less code to maintain and a completely trivial performance boost.
# And there was much rejoicing.

import json


# TODO CODE this should probably be a parameter? YAGNI for now
# see https://www.arangodb.com/2018/07/time-traveling-with-graph-databases/
# in unix epoch ms this is 2255/6/5
_MAX_ADB_INTEGER = 2**53 - 1


def process_nodes(nodeprov, load_version, timestamp, nodes_out):
    """
    Process graph nodes from a provider into a JSON load file for a batch time travelling load.

    This function is only suitable for the initial load in the time travelling database.
    Further loads must use a delta load algorithm.

    Nodes are expected to have an 'id' field containing the node's unique ID.

    nodeprov - the node provider. This is an iterable that returns nodes represented as dicts.
    load_version - the version of the load in which the nodes appear. This is expected to be
      unique per load.
    timestamp - the timestamp at which the nodes will begin to exist.
    nodes_out - a handle to the file where the nodes will be written.
    """
    for n in nodeprov:  # TypeError
        n2 = dict(n)  # Don't modify the incoming data, also TypeError
        n2.update({
            '_key':           n['id'] + '_' + load_version,  # KeyError, TypeError
            'first_version':  load_version,
            'last_version':   load_version,
            'created':        timestamp,
            'expired':        _MAX_ADB_INTEGER
        })
        nodes_out.write(json.dumps(n2) + '\n')  # TypeError


def process_edge(edge, load_version, timestamp):
    """
    Process a graph edge for a batch time travelling load.
    Adds appropriate fields to the edge.

    This function is only suitable for the initial load in the time travelling database.
    Further loads must use a delta load algorithm.

    Edges are expected to have the following fields:
    id - the edge's unique ID.
    from - the unique ID of the vertex from where the edge originates.
    to - the unique ID of the vertex where the edge terminates.

    edge - the edge as a dict.
    load_version - the version of the load in which the edge appears. This is expected to be
      unique per load.
    timestamp - the timestamp at which the edge will begin to exist.

    Returns - the updated edge as a dict.
    """
    edge2 = dict(edge)  # Don't modify the incoming data, TypeError
    edge2.update({
        '_key':             edge['id'] + '_' + load_version,  # KeyError, TypeError
        '_from':            edge['from'] + '_' + load_version,  # KeyError, TypeError
        '_to':              edge['to'] + '_' + load_version,  # KeyError, TypeError
        'first_version':    load_version,
        'last_version':     load_version,
        'created':          timestamp,
        'expired':          _MAX_ADB_INTEGER,
    })
    return edge2


def process_edges(edgeprov, load_version, timestamp, edges_out):  # TODO TEST
    """
    Process graph edges from a provider into a JSON load file for a batch time travelling load.

    This function is only suitable for the initial load in the time travelling database.
    Further loads must use a delta load algorithm.

    Edges are expected to have the following fields:
    id - the edge's unique ID.
    from - the unique ID of the vertex from where the edge originates.
    to - the unique ID of the vertex where the edge terminates.

    edgeprov - the edge provider. This is an iterable that returns edges represented as dicts.
    load_version - the version of the load in which the edges appear. This is expected to be
      unique per load.
    timestamp - the timestamp at which the edges will begin to exist.
    edges_out - a handle to the file where the edges will be written.
    """
    for e in edgeprov:
        e = process_edge(e, load_version, timestamp)
        edges_out.write(json.dumps(e) + '\n')
