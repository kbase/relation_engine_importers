# Data import scripts for the Relation Engine (KBase)

Utilities for reproducible imports into the Relation Engine from various data sources.

To run some of these importers, you need to have the `RE_ADMIN` auth role in your environment
(CI or prod).

This is an experimental utility that imports various data into an ArangoDB graph.

Build status (master):
[![Build Status](https://travis-ci.org/kbase/relation_engine_importers.svg?branch=master)](https://travis-ci.org/kbase/relation_engine_importers)
[![Coverage Status](https://coveralls.io/repos/github/kbase/relation_engine_importers/badge.svg)](https://coveralls.io/github/kbase/relation_engine_importers)

## Setup

For Ubuntu (and possibly other distributions) ensure that the appropriate `python-dev` package
is installed, e.g. `sudo apt install python3.7-dev`. 

With [pipenv](https://github.com/pypa/pipenv) installed, run:

```sh
pipenv install
```

Alternatively, you can use [pyenv](https://github.com/pyenv/pyenv) to manage your python
installations.

## Running tests

To run tests, arangodb must be running locally on the default port with default root credentials.
Then from the repository root:
```
$ pipenv shell
$ export PYTHONPATH=$(pwd):$(pwd)/src/; pytest
```

## Standard loader usage

For loaders in the `src` directory. These loaders may be moved into the `relation_engine`
directory later.

TODO

## Time travelling delta loaders

Time travelling code is in the `relation_engine` directory / package.

It is expected that users running the loaders are familiar with the data types being loaded,
python programming, and KBase infrastructure. For details on the data processing of each loader,
consult the corresponding `parsers.py` class.

There are two types of loaders supported in this repo, bulk loaders and delta loaders.

### Bulk loaders

Bulk loaders create load files suitable for importing into ArangoDB using `arangoimport` and are
used to load the first instance of a graph into the RE.

When loading edges collections, the `--from-collection-prefix` and `--to-collection-prefix`
arguments must be used to specify the name of the node collection(s) to which the edges connect.

### Delta loaders

After the initial load, delta loaders must be used to compare the next graph instance to the
prior instance and calculate and apply the difference between the two graphs to the RE.

For small graphs the delta loader can be used to load the first instance of the graph as well,
but since it will perform numerous unnecessary queries against the database to do the graph
comparison, the bulk loader is typically faster.

### Rolling back a load

Loads can be rolled back with the `relation_engine/batchload/rollback_delta_load.py` script.

### Existing loaders

Use the `--help` option to get instructions for how to use each of the loaders.

#### NCBI Taxonomy Dump Format

Bulk loader: `relation_engine/taxa/ncbi/loaders/ncbi_taxa_bulk_loader.py`  
Delta loader: `relation_engine/taxa/ncbi/loaders/ncbi_taxa_delta_loader.py`

#### GTDB Taxonomy

Since GTDB does not have stable IDs for nodes, the delta loader may not be able to track nodes
correctly across loads.

There is no bulk loader.
Delta loader: `relation_engine/taxa/gtdb/loaders/gtbd_taxa_delta_loader.py`

#### RDP Taxonomy

Since RDP does not have stable IDs for nodes, the delta loader may not be able to track nodes
correctly across loads.

There is no bulk loader.
Delta loader: `relation_engine/taxa/rdp/loaders/rdp_taxa_delta_loadery.py`

#### OBOGraph Ontology JSON Format

There is no bulk loader as ontologies are small enough that an initial load is usually very
fast even with the delta loader.  
Delta loader: `relation_engine/ontologies/obograph/loaders/obograph_delta_loader.py`

The loader has been used to load GO and ENVO ontologies.

### Requirements

* ArangoDB must be version 3.5.0+
* All node and edge collections must have the following persistent indexes
  * `id, expired, created`
  * `expired, created, last_version`

### Creating new loaders

Loaders for NCBI taxonomy are supplied in `relation_engine/ncbi/taxa/loaders` and can be examined
as examples.

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
together to get the load to proceed. There are working implementations in
`relation_engine/ncbi/taxa/loaders`.

For a bulk loader:
* There is a working implementation at `relation_engine/ncbi/taxa/loaders/ncbi_taxa_bulk_loader.py`
* Create the node and edge providers
  * This will depend on the implementation of the providers
* Call `process_nodes` in `relation_engine/batchload/load_utils.py` to create a JSON file
  containing nodes suitable for import via `arangoimport`.
* Call `process_edges` in the same file to create an edge JSON file.
  * Alternatively, if edges are to be loaded into more than one collection, the `process_edge`
    function may be used to process edges individually. The CLI can then determine into which
    file the edge is to be written. There is an example in
    `relation_engine/ncbi/test/ncbi_taxa_bulk_loader_multiple_edges.py`.

For a delta loader:
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