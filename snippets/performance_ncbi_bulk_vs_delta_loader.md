# NCBI Bulk vs Delta loader performance assessment

## Background

Assess whether the NCBI bulk loader, and the bulk loader framework in general, is worth
continued support.

* The only reason the bulk loader exists is that it's theoretically faster than the time
  travelling delta loader for the first load into an empty database.
  * It cannot be used for loads into a database that has any prior time travelling data loads.
  * As such, for production use, it becomes unhelpful almost immediately.
  * It might be useful for test use in cases where a database needs to be built from scratch.
* Only the NCBI dataset has a bulk loader; all other datasets that have time travelling loaders
  exclusively use the delta loader.
  * They are mostly orders of magnitude smaller than the NCBI dataset, in which case loading with
    the delta loader is fast.
* As of this writing the NCBI bulk loader doesn't support release timestamps or registering
  the data load in the load registry collection and so is out of date and needs fixes.

## Test environment

* Berkeley KBase docker03 in a docker container
* Running against the CI 3.9.1/0 ArangoDB installation
  * 3 shards
  * Replication factor = 1
  * Created the collection indexes with the same parameters as the CI database **except** for
    omitting the fulltext index
    * `ncbi_taxon` (document)
    * `ncbi_child_of_taxon` (edge)
    * `ncbi_taxon_merges` (edge)
    * `delta_load_registry` (document)

## Bulk uploader timing

Omitting obvious `cd`s, etc.

```
root@cc09375222e4:/bulk_vs_delta# git clone https://github.com/kbase/relation_engine_importers.git
root@cc09375222e4:/bulk_vs_delta# wget https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/taxdmp_2022-07-01.zip
root@cc09375222e4:/bulk_vs_delta/data# mv ../taxdmp_2022-07-01.zip .
root@cc09375222e4:/bulk_vs_delta/data# unzip taxdmp_2022-07-01.zip 
root@cc09375222e4:/bulk_vs_delta/relation_engine_importers# pip install pipenv
root@cc09375222e4:/bulk_vs_delta/relation_engine_importers# pipenv sync
root@cc09375222e4:/bulk_vs_delta/relation_engine_importers# pipenv shell
(relation_engine_importers) root@cc09375222e4:/bulk_vs_delta/relation_engine_importers# export PYTHONPATH=`pwd`
(relation_engine_importers) root@cc09375222e4:/bulk_vs_delta/relation_engine_importers# echo $PYTHONPATH
/bulk_vs_delta/relation_engine_importers
(relation_engine_importers) root@cc09375222e4:/bulk_vs_delta/relation_engine_importers# date; python relation_engine/taxa/ncbi/loaders/ncbi_taxa_bulk_loader.py --dir /bulk_vs_delta/data/ --load-version test_load --load-timestamp 1657834306000; date
Thu Jul 14 21:32:51 UTC 2022
strain determination round 1
strain determination round 2
strain determination round 3
strain determination round 4
strain determination round 5
Thu Jul 14 21:35:37 UTC 2022
```

166 seconds to prep the load

```
(relation_engine_importers) root@2eb74f64e02b:/bulk_vs_delta/data# date; /arangobenchmark/arango/3.9.1/bin/arangoimport --file ncbi_taxa_nodes.json --server.endpoint tcp://10.58.1.211:8531 --server.username gavin --server.password $ARANGO_PWD_CI --server.database gavin_test --collection ncbi_taxon --threads 5; date
Thu Jul 14 22:54:57 UTC 2022
Connected to ArangoDB 'http+tcp://10.58.1.211:8531, version: 3.9.0, database: 'gavin_test', username: 'gavin'
----------------------------------------
database:               gavin_test
collection:             ncbi_taxon
create:                 no
create database:        no
source filename:        ncbi_taxa_nodes.json
file type:              json
threads:                5
on duplicate:           error
connect timeout:        5
request timeout:        1200
----------------------------------------
Starting JSON import...
2022-07-14T22:54:58Z [80] INFO [9ddf3] {general} processed 25.1 MB (3%) of input file
*snip*
2022-07-14T22:55:23Z [80] INFO [9ddf3] {general} processed 804.2 MB (99%) of input file

created:          2428522
warnings/errors:  0
updated/replaced: 0
ignored:          0
Thu Jul 14 22:55:25 UTC 2022
```

28s to load the nodes

```
(relation_engine_importers) root@2eb74f64e02b:/bulk_vs_delta/data# date; /arangobenchmark/arango/3.9.1/bin/arangoimport --file ncbi_taxa_edges.json --server.endpoint tcp://10.58.1.211:8531 --server.username gavin --server.password $ARANGO_PWD_CI --server.database gavin_test --collection ncbi_child_of_taxon --from-collection-prefix ncbi_taxon --to-collection-prefix ncbi_taxon --threads 5; date
Thu Jul 14 23:00:32 UTC 2022
Connected to ArangoDB 'http+tcp://10.58.1.211:8531, version: 3.9.0, database: 'gavin_test', username: 'gavin'
----------------------------------------
database:               gavin_test
collection:             ncbi_child_of_taxon
from collection prefix: ncbi_taxon
to collection prefix:   ncbi_taxon
create:                 no
create database:        no
source filename:        ncbi_taxa_edges.json
file type:              json
threads:                5
on duplicate:           error
connect timeout:        5
request timeout:        1200
----------------------------------------
Starting JSON import...
2022-07-14T23:00:32Z [96] INFO [9ddf3] {general} processed 18.8 MB (3%) of input file
*snip*
2022-07-14T23:01:08Z [96] INFO [9ddf3] {general} processed 606.0 MB (99%) of input file

created:          2428521
warnings/errors:  0
updated/replaced: 0
ignored:          0
Thu Jul 14 23:01:11 UTC 2022
```

39s to load the edges

TOTAL = 233s to perform the load

## Delta uploader timing

Truncated the collections first.

```
(relation_engine_importers) root@2eb74f64e02b:/bulk_vs_delta/relation_engine_importers# date; python relation_engine/taxa/ncbi/loaders/ncbi_taxa_delta_loader.py --dir /bulk_vs_delta/data/ --load-registry-collection delta_load_registry --arango-url http://10.58.1.211:8531 --database gavin_test --node-collection ncbi_taxon --edge-collection ncbi_child_of_taxon --merge-edge-collection ncbi_taxon_merges --load-version test_load --load-timestamp 1657834306000 --release-timestamp 1657834306000 --user gavin; date
Fri Jul 15 00:41:28 UTC 2022
Password: 
strain determination round 1
strain determination round 2
strain determination round 3
strain determination round 4
strain determination round 5
Fri Jul 15 00:54:14 UTC 2022
```

766 seconds for the entire load = ~3.3x slower

Note that the bulk loader used 5 threads and the delta loader is currently single threaded,
which might explain some of the difference.

In the RE tech review meeting on 7/15/22, a decision was made to remove the bulk loader.