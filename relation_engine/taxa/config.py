"""
A configuration parser for taxa delta loaders. The configuration is expected to be in TOML
(https://toml.io/en/) format.
"""

import os
import tomli  # TODO swap to stdlib in py 3.11
from frozendict import frozendict
from typing import Optional, BinaryIO
from pathlib import Path

# This could potentially be extended to the obograph loader as well, but would require more
# inputs. Maybe extend? Might be better to duplicate

# Since this is KBase internal code we can be a bit less compassionate re good
# error messages, e.g. throwing any TOML parsing errors, etc.
# As a result we get slightly less code to maintain and a completely trivial performance boost.
# And there was much rejoicing.

_SEC_INPUTS = "Inputs"
_SEC_ARANGO = "Arango"
_SEC_VERSIONING = "Versioning"
_ENV_ARANGO_PASSWORD = "ARANGO_PWD"


class DeltaLoaderConfig:
    """
    The delta load configuration parsed from a TOML configuration file. Once initialized, this
    class will contain the fields:

    inputs: dict[str, Path] - a dict with an entry for each input key provided in the
        constructor.

    url: str - the URL of an arango coordinator.
    database: str - the name of the ArangoDB database to update.
    user: str | None - the username, if any, of the user name to use when connecting to
         ArangoDB.
    password: str | None - the password for the user. Present IFF the user is present.
    load_registry_collection: str - The name of the ArangoDB collection in which to register
        the load.
    node_collection: str - the name of the ArangoDB collection in which to load taxa nodes.
    edge_collection: str - the name of the ArangoDB collection in which to load taxa edges.
    merge_edge_collection: str | None - the name of the ArangoDB collection in which to
        load merge edges.

    load_version: str - the version of the load.
    load_timestamp: int - the timestamp of the load in epoch milliseconds, e.g. when the load
        will start to exist in the database.
    release_timestamp: int - the timestamp, in unix epoch milliseconds, when the data was
        released at the source.
    """

    def __init__(
            self,
            config_file: BinaryIO,
            input_keys: list[str],
            require_merge_collection: bool = False):
        """
        Create the configuration parser.

        config_file - an open file-like object, opened in binary mode, containing the TOML
            config file data.
        input_keys - a list of keys for entries in the configuration that will
            specify a path to an input file or directory. They are expected to be in the
            "Inputs" section of the configuration.
        require_merge_collection - if true, throw an error is a merge collection is not specified.
        """
        if not config_file:
            raise ValueError("config_file is required")
        if not input_keys:
            raise ValueError("at least one input key is required")
        config = tomli.load(config_file)
        # I feel like there ought to be a lib to do this kind of stuff... jsonschema doesn't
        # quite do what I want
        _check_missing_section(config, _SEC_INPUTS)
        _check_missing_section(config, _SEC_ARANGO)
        _check_missing_section(config, _SEC_VERSIONING)
        inputs = {}
        for key in input_keys:
            if not config[_SEC_INPUTS].get(key):
                raise ValueError(f"Missing input key {key} in section {_SEC_INPUTS}")
            inputs[key] = Path(config[_SEC_INPUTS][key].strip())
        self.inputs = frozendict(inputs)
        self.url = _get_string_required(config, _SEC_ARANGO, "url")
        self.database = _get_string_required(config, _SEC_ARANGO, "database")
        self.user = _get_string_optional(config, _SEC_ARANGO, "username")
        self.password = _get_string_optional(config, _SEC_ARANGO, "password")
        if self.user and not self.password:
            p = os.environ.get(_ENV_ARANGO_PASSWORD)
            self.password = p.strip() if p else None
            if not self.password:
                raise ValueError(
                    f"If username is present in the {_SEC_ARANGO} section, password must be "
                    + f"present either in the config file or the {_ENV_ARANGO_PASSWORD} "
                    + "environment variable")
        self.load_registry_collection = _get_string_required(
            config, _SEC_ARANGO, "load-registry-collection")
        self.node_collection = _get_string_required(config, _SEC_ARANGO, "node-collection")
        self.edge_collection = _get_string_required(config, _SEC_ARANGO, "edge-collection")
        f = _get_string_required if require_merge_collection else _get_string_optional
        self.merge_edge_collection = f(config, _SEC_ARANGO, "merge-edge-collection")
        self.load_version = _get_string_required(config, _SEC_VERSIONING, "load-version")
        self.load_timestamp = _get_int_required(config, _SEC_VERSIONING, "load-timestamp")
        self.release_timestamp = _get_int_required(config, _SEC_VERSIONING, "release-timestamp")


def _check_missing_section(config, section):
    if section not in config:
        raise ValueError(f"Missing section {section}")


# assumes section exists
def _get_string_required(config, section, key) -> str:
    putative = _get_string_optional(config, section, key)
    if not putative:
        raise ValueError(f"Missing value for key {key} in section {section}")
    return putative


# assumes section exists
def _get_string_optional(config, section, key) -> Optional[str]:
    putative = config[section].get(key)
    if putative is None or not putative.strip():  # typechecks a string here effectively
        return None
    return putative.strip()


# assumes section exists
def _get_int_required(config, section, key) -> int:
    putative = config[section].get(key)
    if putative is None:
        raise ValueError(f"Missing value for key {key} in section {section}")
    if isinstance(putative, int):
        return putative
    if isinstance(putative, float):
        if putative.is_integer():
            return int(putative)
        raise ValueError(
            f"Illegal value for key {key} in section {section}, which expects an integer: "
            + f"{putative}")
    raise ValueError(
        f"Illegal type for key {key} in section {section}, which expects an integer: "
        + f"{type(putative).__name__}")
