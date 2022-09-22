# Data import scripts for the Relation Engine (KBase)

Utilities for reproducible imports into the Relation Engine from various data sources.

To run some of these importers, you need to have the `RE_ADMIN` auth role in your environment
(CI or prod).

This is an experimental utility that imports various data into an ArangoDB graph.

Build status (master):
[![Build Status](https://travis-ci.org/kbase/relation_engine_importers.svg?branch=master)](https://travis-ci.org/kbase/relation_engine_importers)
[![codecov](https://codecov.io/gh/kbase/relation_engine_importers/branch/master/graph/badge.svg?token=YUiBQ5QX99)](https://codecov.io/gh/kbase/relation_engine_importers)

NOTE: Coverage only includes files that are at least touched by tests. There are many files that
have no tests at all, and so the actual coverage of this repo is much lower than reported.

## Setup

Install Python 3.10, optionally using pyenv: https://github.com/pyenv/pyenv

Then install [pipenv](https://github.com/pypa/pipenv) and run:

```sh
pipenv sync --dev
```

## Running tests

To run tests, `arangodb` must be running locally on the default port with default root credentials.
You can run `arangodb` using docker-compose with `docker-compse up`. However, we have found that
running `arangodb` outside the docker container is ~10x faster for reasons that are currently
unknown. Assuming a tarball based install with the `bin` directory of the tarball on the path, this
command line will launch `arangodb` as a daemon using `./temparagodata` as its data directory:

```sh
arangodb start --server.arangod=arangod --starter.mode single --starter.data-dir ./temparangodata
```

Note that you may have to increase the maximum open file count for your OS to 8192 in order for
`arangodb` to start.

Then from the repository root:

```sh
make test
```

To stop arangodb:
```sh
arangodb stop
```

## Time travelling delta loaders

Time travelling code is in the `relation_engine` directory / package.

It is expected that users running the loaders are familiar with the data types being loaded,
python programming, and KBase infrastructure. For details on the data processing of each loader,
consult the corresponding `parsers.py` class.

See [the description of the delta load algorithm](./delta_load_algorithm.md) for details on how
the loaders operate.

### Rolling back a load

Loads can be rolled back with the `relation_engine/batchload/rollback_delta_load.py` script.

### Existing loaders

Use the `--help` option to get instructions for how to use each of the loaders.

#### NCBI Taxonomy Dump Format

`relation_engine/taxa/ncbi/loaders/ncbi_taxa_delta_loader.py`

#### GTDB Taxonomy

Since GTDB does not have stable IDs for nodes, the delta loader may not be able to track nodes
correctly across loads.

`relation_engine/taxa/gtdb/loaders/gtbd_taxa_delta_loader.py`

#### RDP Taxonomy

Since RDP does not have stable IDs for nodes, the delta loader may not be able to track nodes
correctly across loads.

`relation_engine/taxa/rdp/loaders/rdp_taxa_delta_loadery.py`

#### OBOGraph Ontology JSON Format

`relation_engine/ontologies/obograph/loaders/obograph_delta_loader.py`

The loader has been used to load GO and ENVO ontologies.

### Requirements

* ArangoDB must be version 3.5.0+
* All node and edge collections must have the following persistent indexes
  * `id, expired, created`
  * `expired, created, last_version`

### Creating new loaders

A loader for NCBI taxonomy is supplied in `relation_engine/ncbi/taxa/loaders` and can be examined
as an example.

To create a new loader, at minimum an edge provider, a node provider, and a CLI must be
created.

#### Edge and node providers

The providers are simply iteratables that provide edges and nodes as a `dict`. There are working
implementations in `relation_engine\ncbi\taxa\parsers.py`.

Nodes must contain an `id` field. This ID must uniquely identify the node in the graph and
be stable from version to version of the graph (unless the node is deleted or merged.)

Edges must contain `id`, `from`, and `to` fields. The ID has the same semantics as the node ID,
and the `from` and `to` fields contain the `id`s of the nodes where the edge originates and
terminates.

If the graph contains merge edges, a merge edge provider can be constructed in the same way as a
standard edge provider, where `from` is the ID of the merged node.

Otherwise, all other fields in the nodes and edges are preserved and inserted into the RE as is,
except for a few special fields:

|Field|Use|
|-----|---|
|`_rev`|ArangoDB internal use|
|`_key`|ArangoDB internal use|
|`_id`|ArangoDB internal use|
|`_from`|ArangoDB internal use|
|`_to`|ArangoDB internal use|
|`_collection`|Specify the collection that will contain an edge. This field is ignored for nodes and merge edges. If there is no value for this field, the default edge collection is used.|
|`last_version`| the ID of the last load in which the edge or node appeared.|
|`first_version`| the ID of the first load in which the edge or node appeared.|
|`created`| the timestamp, in unix epoch milliseconds, when the edge or node came into existence.|
|`expired`| the timestamp, in unix epoch milliseconds, when the edge or node was deleted.|
|`release_created`| the timestamp, in unix epoch milliseconds, when the edge or node came into existence at the data source.|
|`release_expired`| the timestamp, in unix epoch milliseconds, when the edge or node was deleted at the data source.|


These fields, with the exception of `_collection`, will be overwritten if included in the `dicts`
emitted from the providers. In the case of edges, `_collection` will be removed from the edge
prior to inserting the edge into the appropriate collection.

In the context of the RE, it is expected that the combination of an ID and a timestamp uniquely
identifies a node or edge. Thus, for a particular ID the `created` -> `expired` range should not
overlap for nodes in separate loads.

#### CLI

The CLI code takes user arguments (such as the load version and timestamp) and puts all the parts
together to get the load to proceed.

* There is a working implementation at
  `relation_engine/ncbi/taxa/loaders/ncbi_taxa_delta_loader.py`
* Create the node and edge providers.
  * This will depend on the implementation of the providers
  * Optionally, create a merge edge provider
* Create an instance of the `ArangoBatchTimeTravellingDB` class. This class is located in
  `relation_engine/batchload/time_travelling_database.py`
  * If not using the `_collection` field to specify the collection to which an edge belongs for
    all edges, the default edge collection **MUST** be specified. If the `_collection` field
    is missing for an edge, the default edge collection will be used.
  * If multiple edge collections are to be used, they must be provided in the `edge_collections`
    argument. The default edge collection, if any, may be omitted from this list.
  * If a merge provider is available, specify the merge collection in the `merge_collection`
    argument.
* Call `load_graph_delta` in `relation_engine/batchload/delta_load.py`.
  * If a merge provider is available, specify the provider in the `merge_source` argument.

### Prior development and scripts

Development of the delta loader previously took place in
https://github.com/kbaseIncubator/relation_engine_incubator. There are also possibly helpful
one-off scripts there.

### TODO

* Much of the code is not well tested.
* Handling merge edges in the delta loader could be improved.
  * Merge edges are never expired.
  * Currently only handles merge edges where
    * The merged node was present in the prior load and
    * The target node is present in the current load.

## Development

When developing improvements to current loaders or adding new loaders to the repo, increment the
[semantic version](https://semver.org/) in `relation_engine/version.py`. Currently only the
GTDB and NCBI taxa loaders have an option to print the version - if changes are made to other
loaders add the ability to print the version there as well.