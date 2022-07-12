from copy import deepcopy
from io import StringIO
from relation_engine.batchload.load_utils import process_nodes


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


def check_json_list_file_contents(expected_lines, infile):
    index = 0
    for line in infile:
        assert expected_lines[index] == line
        index += 1
    assert len(expected_lines) == index
