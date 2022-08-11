import os
from io import BytesIO
from pathlib import Path
from pytest import raises
from tomli import TOMLDecodeError

from relation_engine.taxa.config import DeltaLoaderConfig
from relation_engine.test.testing_helpers import assert_exception_correct

_BASIC_CONFIG = "\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "http://localhost:12354"',
        'database = "mydb"',
        'load-registry-collection = "lrc"',
        'node-collection = "nodes"',
        'edge-collection = "edges"',
        "[Versioning]",
        'load-version = "lver"',
        "load-timestamp = 12365",
        "release-timestamp = -16000",
    ]).encode("utf-8")


def test_minimal_config_success():
    cfgfile = BytesIO(_BASIC_CONFIG)
    cfg = DeltaLoaderConfig(cfgfile, ["input_file"])

    _check_config(
        cfg=cfg,
        inputs={"input_file": Path("./bar.txt")},
        url="http://localhost:12354",
        database="mydb",
        user=None,
        password=None,
        load_registry_collection="lrc",
        node_collection="nodes",
        edge_collection="edges",
        merge_edge_collection=None,
        load_version="lver",
        load_timestamp=12365,
        release_timestamp=-16000,
        )


def test_minimal_config_whitespace_success():
    # Include optional keys with whitespace entries
    cfgfile = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "http://localhost:12354"',
        'database = "mydb"',
        'username = "    \t    "',
        'password = "    \t    "',
        'load-registry-collection = "lrc"',
        'node-collection = "nodes"',
        'edge-collection = "edges"',
        'merge-edge-collection = "    \t    "',
        "[Versioning]",
        'load-version = "lver"',
        "load-timestamp = 12365.0",
        "release-timestamp = -16000",
    ]).encode("utf-8"))
    cfg = DeltaLoaderConfig(cfgfile, ["input_file"])

    _check_config(
        cfg=cfg,
        inputs={"input_file": Path("./bar.txt")},
        url="http://localhost:12354",
        database="mydb",
        user=None,
        password=None,
        load_registry_collection="lrc",
        node_collection="nodes",
        edge_collection="edges",
        merge_edge_collection=None,
        load_version="lver",
        load_timestamp=12365,
        release_timestamp=-16000,
        )


def test_maximal_config_success():
    cfgfile = BytesIO("\n".join([
        "[Inputs]",
        '     input_file    =     "    ./bar.txt   "    ',
        'other_file = "/tmp/usera/misc/schoolwork/CBS101a/homework1/tortoises_in_the_nude.mp4"',
        "[Arango]",
        '    url    =     "     https://hoorayitspirateday.com    "   \t  ',
        '\tdatabase\t = \t"\tmyotherdb\t"\t',
        '    username    =     "    \t  user1   "   \t  ',
        ' password  =  " pwd1 " ',
        '    \t  load-registry-collection \t   =   \t  "  \t  loading...  \t "  \t',
        '     node-collection    =    "    mynodes   "  ',
        ' edge-collection  =  " myedges " ',
        '\tmerge-edge-collection\t =\t "\tmerges\t"\t',
        "[Versioning]",
        '   load-version    =    "    this is a version   "    ',
        " \t load-timestamp    =     \t  6    \t",
        "   release-timestamp  =  42.000 ",
    ]).encode("utf-8"))
    cfg = DeltaLoaderConfig(cfgfile, ["input_file", "other_file"], require_merge_collection=True)

    _check_config(
        cfg=cfg,
        inputs={
            "input_file": Path("./bar.txt"),
            "other_file": Path(
                "/tmp/usera/misc/schoolwork/CBS101a/homework1/tortoises_in_the_nude.mp4"),
        },
        url="https://hoorayitspirateday.com",
        database="myotherdb",
        user="user1",
        password="pwd1",
        load_registry_collection="loading...",
        node_collection="mynodes",
        edge_collection="myedges",
        merge_edge_collection="merges",
        load_version="this is a version",
        load_timestamp=6,
        release_timestamp=42,
        )


def test_config_with_env_var_password_success():
    pwdold = os.environ.get("ARANGO_PWD")
    os.environ["ARANGO_PWD"] = "    mypassword    \t  "
    try:
        cfgfile = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "http://localhost:12354"',
            'database = "mydb"',
            'username = "   foo   "',
            'password = "      "',
            'load-registry-collection = "lrc"',
            'node-collection = "nodes"',
            'edge-collection = "edges"',
            "[Versioning]",
            'load-version = "lver"',
            "load-timestamp = 12365.0",
            "release-timestamp = -16000",
        ]).encode("utf-8"))
        cfg = DeltaLoaderConfig(cfgfile, ["input_file"])

        _check_config(
            cfg=cfg,
            inputs={"input_file": Path("./bar.txt")},
            url="http://localhost:12354",
            database="mydb",
            user="foo",
            password="mypassword",
            load_registry_collection="lrc",
            node_collection="nodes",
            edge_collection="edges",
            merge_edge_collection=None,
            load_version="lver",
            load_timestamp=12365,
            release_timestamp=-16000,
            )
    finally:
        if pwdold is None:
            del os.environ["ARANGO_PWD"]
        else:
            os.environ["ARANGO_PWD"] = pwdold


def _check_config(
        cfg,
        inputs,
        url,
        database,
        user,
        password,
        load_registry_collection,
        node_collection,
        edge_collection,
        merge_edge_collection,
        load_version,
        load_timestamp,
        release_timestamp):
    assert cfg.inputs == inputs
    assert cfg.url == url
    assert cfg.database == database
    assert cfg.user == user
    assert cfg.password == password
    assert cfg.load_registry_collection == load_registry_collection
    assert cfg.node_collection == node_collection
    assert cfg.edge_collection == edge_collection
    assert cfg.merge_edge_collection == merge_edge_collection
    assert cfg.load_version == load_version
    assert cfg.load_timestamp == load_timestamp
    assert cfg.release_timestamp == release_timestamp


def test_immutability():
    '''
    I mean, the whole stinking class is mutable, but we're putting the input files in a
    frozendict and by gawd, I'm going to test that we're putting the input files in a frozendict
    '''
    cfgfile = BytesIO(_BASIC_CONFIG)
    cfg = DeltaLoaderConfig(cfgfile, ["input_file"])

    with raises(Exception) as got:
        cfg.inputs["foo"] = "bar"
    assert_exception_correct(got.value, TypeError(
        "'frozendict.frozendict' object does not support item assignment"))


def test_fail_no_file():
    _fail_config(None, ['foo'], False, ValueError("config_file is required"))


def test_fail_no_keys():
    f = BytesIO(b"")
    _fail_config(f, None, False, ValueError("at least one input key is required"))
    _fail_config(f, [], False, ValueError("at least one input key is required"))


def test_fail_toml_error():
    # I'm sure there's tons more possible TOML errors, but we're not here to test their code
    # for them, are we?
    f = BytesIO(b"input_file =  \ninput_file2 = bar")
    _fail_config(f, ["inputfile"], False, TOMLDecodeError("Invalid value (at line 1, column 15)"))


def test_fail_missing_inputs_section():
    f = BytesIO("\n".join([
        'input_file = "./bar.txt"',
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError("Missing section Inputs"))


def test_fail_missing_arango_section():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError("Missing section Arango"))


def test_fail_missing_versioning_section():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "https://foo.com"',
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError("Missing section Versioning"))


def test_fail_missing_input_key():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        'input_file2 = "./foo.txt"',
        "[Arango]",
        "[Versioning]",
    ]).encode("utf-8"))
    _fail_config(f, ["inputfile"], False, ValueError(
        "Missing input key inputfile in section Inputs"))


def test_fail_missing_url():
    for url in ["", 'url = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            url,
            'database = "mydb"',
            "[Versioning]",
            'load-version = "ver"',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], False, ValueError(
            "Missing value for key url in section Arango"))


def test_fail_missing_database():
    for db in ["", 'database = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "https://foo.com"',
            db,
            "[Versioning]",
            'load-version = "ver"',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], False, ValueError(
            "Missing value for key database in section Arango"))


def test_fail_missing_password():
    for p in ["", 'password = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "https://foo.com"',
            'database = "db"',
            'username = "pwd is required if user is misssing"',
            p,
            "[Versioning]",
            'load-version = "ver"',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], False, ValueError(
            "If username is present in the Arango section, password must be present "
            + "either in the config file or the ARANGO_PWD environment variable"))


def test_fail_missing_load_registry_collection():
    for lrc in ["", 'load-registry-collection = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "https://foo.com"',
            'database = "db"',
            lrc,
            "[Versioning]",
            'load-version = "ver"',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], False, ValueError(
            "Missing value for key load-registry-collection in section Arango"))


def test_fail_missing_node_collection():
    for n in ["", 'node-collection = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "https://foo.com"',
            'database = "db"',
            'load-registry-collection = "lrc"',
            n,
            "[Versioning]",
            'load-version = "ver"',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], False, ValueError(
            "Missing value for key node-collection in section Arango"))


def test_fail_missing_edge_collection():
    for e in ["", 'edge-collection = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "https://foo.com"',
            'database = "db"',
            'load-registry-collection = "lrc"',
            'node-collection = "node"',
            e,
            "[Versioning]",
            'load-version = "ver"',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], False, ValueError(
            "Missing value for key edge-collection in section Arango"))


def test_fail_missing_merge_collection():
    for m in ["", 'merge-edge-collection = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "https://foo.com"',
            'database = "db"',
            'load-registry-collection = "lrc"',
            'node-collection = "node"',
            'edge-collection = "edge"',
            m,
            "[Versioning]",
            'load-version = "ver"',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], True, ValueError(
            "Missing value for key merge-edge-collection in section Arango"))


def test_fail_missing_load_version():
    for lv in ["", 'load-version = "    \t  "']:
        f = BytesIO("\n".join([
            "[Inputs]",
            'input_file = "./bar.txt"',
            "[Arango]",
            'url = "https://foo.com"',
            'database = "db"',
            'load-registry-collection = "lrc"',
            'node-collection = "node"',
            'edge-collection = "edge"',
            "[Versioning]",
            lv,
            'load-timestamp = 1',
        ]).encode("utf-8"))
        _fail_config(f, ["input_file"], False, ValueError(
            "Missing value for key load-version in section Versioning"))


def test_fail_missing_load_timestamp():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "https://foo.com"',
        'database = "db"',
        'load-registry-collection = "lrc"',
        'node-collection = "node"',
        'edge-collection = "edge"',
        "[Versioning]",
        'load-version = "v1"',
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError(
        "Missing value for key load-timestamp in section Versioning"))


def test_fail_float_load_timestamp():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "https://foo.com"',
        'database = "db"',
        'load-registry-collection = "lrc"',
        'node-collection = "node"',
        'edge-collection = "edge"',
        "[Versioning]",
        'load-version = "v1"',
        'load-timestamp = 3.14'
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError(
        "Illegal value for key load-timestamp in section Versioning, which expects an integer: "
        + "3.14"))


def test_fail_bad_type_load_timestamp():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "https://foo.com"',
        'database = "db"',
        'load-registry-collection = "lrc"',
        'node-collection = "node"',
        'edge-collection = "edge"',
        "[Versioning]",
        'load-version = "v1"',
        'load-timestamp = []'
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError(
        "Illegal type for key load-timestamp in section Versioning, which expects an integer: "
        + "list"))


def test_fail_missing_release_timestamp():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "https://foo.com"',
        'database = "db"',
        'load-registry-collection = "lrc"',
        'node-collection = "node"',
        'edge-collection = "edge"',
        "[Versioning]",
        'load-version = "v1"',
        "load-timestamp = 89"
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError(
        "Missing value for key release-timestamp in section Versioning"))


def test_fail_float_release_timestamp():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "https://foo.com"',
        'database = "db"',
        'load-registry-collection = "lrc"',
        'node-collection = "node"',
        'edge-collection = "edge"',
        "[Versioning]",
        'load-version = "v1"',
        "load-timestamp = 89",
        "release-timestamp = 6.02"
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError(
        "Illegal value for key release-timestamp in section Versioning, which expects an integer: "
        + "6.02"))


def test_fail_bad_type_release_timestamp():
    f = BytesIO("\n".join([
        "[Inputs]",
        'input_file = "./bar.txt"',
        "[Arango]",
        'url = "https://foo.com"',
        'database = "db"',
        'load-registry-collection = "lrc"',
        'node-collection = "node"',
        'edge-collection = "edge"',
        "[Versioning]",
        'load-version = "v1"',
        "load-timestamp = 89",
        'release-timestamp = "4"'
    ]).encode("utf-8"))
    _fail_config(f, ["input_file"], False, ValueError(
        "Illegal type for key release-timestamp in section Versioning, which expects an integer: "
        + "str"))


def _fail_config(config_file, input_keys, require_merge_collection, expected):
    with raises(Exception) as got:
        DeltaLoaderConfig(config_file, input_keys, require_merge_collection)
    assert_exception_correct(got.value, expected)
