from copy import deepcopy
from io import StringIO
from relation_engine.batchload.load_utils import process_nodes, process_edge, process_edges


_MAX_ADB_INT = 9007199254740991


def test_process_nodes_noop():
    outfile = StringIO()
    process_nodes([], 'ver', 1, outfile)
    assert outfile.getvalue() == ''


def test_process_nodes():
    outfile = StringIO()
    nodes = [
        {
            'id': "baz"
        },
        {
            'id': 'bat',
            'some_field': 'some_value',
            'some_other_field': 'some_other_value'
        }
    ]
    nodescopy = deepcopy(nodes)
    process_nodes(nodes, 'load-ver', 78, outfile)

    assert nodescopy == nodes

    expected = [
        '{"id": "baz", "_key": "baz_load-ver", "first_version": "load-ver", '
        + f'"last_version": "load-ver", "created": 78, "expired": {_MAX_ADB_INT}}}\n',
        '{"id": "bat", "some_field": "some_value", "some_other_field": "some_other_value", '
        + '"_key": "bat_load-ver", "first_version": "load-ver", "last_version": "load-ver", '
        + f'"created": 78, "expired": {_MAX_ADB_INT}}}\n',
    ]

    outfile.seek(0)
    check_json_list_file_contents(expected, outfile)


def test_process_edge_minimal():
    edge = {
        'id': 'foo',
        'from': 'yermums',
        'to': 'thechipshop',
    }
    edgecopy = dict(edge)
    pedge = process_edge(edge, 'loadversion', 42)

    assert edgecopy == edge
    expected = {
        'id': 'foo',
        'from': 'yermums',
        'to': 'thechipshop',
        '_key': 'foo_loadversion',
        '_from': 'yermums_loadversion',
        '_to': 'thechipshop_loadversion',
        'first_version': 'loadversion',
        'last_version': 'loadversion',
        'created': 42,
        'expired': _MAX_ADB_INT,
    }
    assert expected == pedge


def test_process_edge():
    edge = {
        'id': 'fad',
        'from': 'yerdads',
        'to': 'the_rat_and_grommet',
        'alright': 'innit',
        'gorblimey': 'guvnor',
    }
    edgecopy = dict(edge)
    pedge = process_edge(edge, 'this_is_a_version', 84)

    assert edgecopy == edge
    expected = {
        'id': 'fad',
        'from': 'yerdads',
        'to': 'the_rat_and_grommet',
        'alright': 'innit',
        'gorblimey': 'guvnor',
        '_key': 'fad_this_is_a_version',
        '_from': 'yerdads_this_is_a_version',
        '_to': 'the_rat_and_grommet_this_is_a_version',
        'first_version': 'this_is_a_version',
        'last_version': 'this_is_a_version',
        'created': 84,
        'expired': _MAX_ADB_INT,
    }
    assert expected == pedge


def test_process_edges_noop():
    outfile = StringIO()
    process_edges([], 'ver', 1, outfile)
    assert outfile.getvalue() == ''


def test_process_edges():
    outfile = StringIO()
    edges = [
        {
            'id': "baz",
            'from': 'my_happy_place',
            'to': 'cursed_reality',
        },
        {
            'id': 'bat',
            'from': 'fryingpan',
            'to': 'fire',
            'also_any_other': 'cliches',
            'you_might_like': 'to_include',
        }
    ]
    edgescopy = deepcopy(edges)
    process_edges(edges, 'lversion', 126, outfile)

    assert edgescopy == edges

    expected = [
        '{"id": "baz", "from": "my_happy_place", "to": "cursed_reality", "_key": "baz_lversion", '
        + '"_from": "my_happy_place_lversion", "_to": "cursed_reality_lversion", '
        + '"first_version": "lversion", "last_version": "lversion", "created": 126, '
        + '"expired": 9007199254740991}\n',
        '{"id": "bat", "from": "fryingpan", "to": "fire", "also_any_other": "cliches", '
        + '"you_might_like": "to_include", "_key": "bat_lversion", "_from": "fryingpan_lversion", '
        + '"_to": "fire_lversion", "first_version": "lversion", "last_version": "lversion", '
        + '"created": 126, "expired": 9007199254740991}\n'
    ]

    outfile.seek(0)
    check_json_list_file_contents(expected, outfile)


def check_json_list_file_contents(expected_lines, infile):
    index = 0
    for line in infile:
        assert expected_lines[index] == line
        index += 1
    assert len(expected_lines) == index
