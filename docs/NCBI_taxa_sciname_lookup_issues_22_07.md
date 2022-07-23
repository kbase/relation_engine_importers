# NCBI taxonomy scientific lookup issues as of 2022/07

## Background

* The NCBI taxa loader was originally written such that nodes with a rank of `no rank` that
  were children of a `species` or a `subspecies` node were flagged with a `strain` boolean.
  Furthermore, any `no rank` children of `strain` flagged nodes were flagged as a strain.
  * This was to handle cases of nodes that were below-species based on their position in the
    tree but had no rank
  * Note that this missed the below-species ranks of `forma` and `varietas`, and so some
    `no rank` nodes that should have been flagged as strains may have been missed
    * As of 2019/10, the scope of this problem was probably relatively small:
      * `species`: 1766664
      * `no rank`: 262419
      * `subspecies`: 23860
      * `varietas`: 8007
      * `forma`: 538
* The original RE scientific name lookup query allowed specifying the ranks of interest, as well
  as whether strains (e.g. flagged `no rank` nodes) should be included:
  * [taxonomy_search_sci_name](https://github.com/kbase/relation_engine/blob/develop/spec/stored_queries/taxonomy/taxonomy_search_sci_name.yaml)
  * First commit is 2000/3/13
  * This would be correct other than the missing `no rank` nodes under `varietas` or `forma`,
    assuming all species-and-below ranks were provided to the API
    * E.g. `species`, `subspecies`, `varietas`, `forma`
  * However, the [first implementation of the query](https://github.com/kbaseapps/RAST_SDK/pull/73/files) only specified the `species` rank and the `strain` boolean, missing 3 below-species ranks
* A new RE query was made to speed up the search, hardcoding the lookup to `species` rank and the
  `strain` booleans
  * [taxonomy_search_species](https://github.com/kbase/relation_engine/blob/develop/spec/stored_queries/taxonomy/taxonomy_search_species.yaml)
  * First commit is 2020/4/1
  * This misses all `subspecies`, `varietas`, and `forma` nodes as well as the `no rank` nodes
    that were not flagged correctly by the loader (see above)
  * This approach was copied when developing the improved queries that superceded the query above,
    except that the included ranks are both `species` and `strain`:
    * [taxonomy_search_species_strain](https://github.com/kbase/relation_engine/blob/develop/spec/stored_queries/taxonomy/taxonomy_search_species_strain.yaml)
    * [taxonomy_search_species_strain_no_sort](https://github.com/kbase/relation_engine/blob/develop/spec/stored_queries/taxonomy/taxonomy_search_species_strain_no_sort.yaml)
* As of 2022/07, many new ranks (including an explicit `strain` rank) have been added below the
  species level, and well as more non-hierarchical ranks:
  * https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7408187/#sup1
  * Changes since 2019/10 when the loader was last altered:
    * Non-hierarchical:
      * `clade`: 915
      * `environmental samples`: 0
      * `incertae sedis`: 0
      * `unclassified <name>`: 0
      * `no rank` (pre-existing): 231894
    * Hierarchical:
      * `species` (pre-existing): 1984066
      * `forma specialis`: 742
      * `subspecies` (pre-existing): 26925
      * `varietas` (pre-existing): 9200
      * `morph`: 12
      * `subvariety`: 0
      * `forma` (pre-existing): 626
      * `serogroup`:140
      * `pathogroup`: 5
      * `serotype`: 1240
      * `biotype`: 17
      * `genotype`: 20
      * `strain`: 45139
      * `isolate`: 1322
* There are currently six KBase apps that use the scientific name lookup query:
  * `kb_uploadmethods`
    * [import GFF genome](https://github.com/kbaseapps/kb_uploadmethods/blob/d67ff71a675aed5566d257c267689ea0d2a4a8b0/ui/narrative/methods/import_gff_fasta_as_genome_from_staging/spec.json#L110-L116)
    * [import Genbank genome](https://github.com/kbaseapps/kb_uploadmethods/blob/d67ff71a675aed5566d257c267689ea0d2a4a8b0/ui/narrative/methods/import_genbank_as_genome_from_staging/spec.json#L127-L133)
    * Both use `taxonomy_re_api.search_species`
    * Which uses the newest taxonomy_search_species_strain* queries
  * `RAST_SDK` 
    * [annotate genome assembly](https://github.com/kbaseapps/RAST_SDK/blob/f21473955c1394adf25fdaed838a8d84b8950b8c/ui/narrative/methods/annotate_genome_assembly/spec.json#L63-L69)
    * [annotate contig](https://github.com/kbaseapps/RAST_SDK/blob/f21473955c1394adf25fdaed838a8d84b8950b8c/ui/narrative/methods/annotate_contigset/spec.json#L32-L38)
    * [annotate contigs](https://github.com/kbaseapps/RAST_SDK/blob/f21473955c1394adf25fdaed838a8d84b8950b8c/ui/narrative/methods/annotate_contigsets/spec.json#L43-L49)
    * All use `taxonomy_re_api.search_species`
    * Which uses the newest taxonomy_search_species_strain* queries
  * `ProkkaAnnotation`
    * [annotate contigs](https://github.com/kbaseapps/ProkkaAnnotation/blob/1967e07320b1898db0c6998bb4549b7f1187e5a8/ui/narrative/methods/annotate_contigs/spec.json#L35-L41)
    * Uses `taxonomy_re_api.search_taxa`
    * Which uses the first, slow taxonomy_search_sci_name query

## Issues
* The loader does not properly mark all `no rank` nodes that are below-species with the
  `strain` boolean.
  * It originally missed the `varietas` and `forma` ranks when marking nodes
  * There are now 10 new below-species ranks
* The loader's `strain` boolean is misnamed
  * It really means "nodes that are below species but have no rank", which is not necessarily a
    strain
  * It now conflicts, and may cause confusion with, the NCBI `strain` rank
* The loader does not account for the new `clade` non-hierarchical rank (and other currently
  unused hierarchical ranks)
* The modification to the query to hardcode ranks to `species` only (and in the improved query,
  `species` and `strain`) excludes many ranks, both present at the time of the first modification
  and added since then.
  * Furthermore, as we can see, hardcoding the ranks is not future proof.

## Fixes

### To be done regardless of the option chosen below

* Alter the loader to fail with an appropriate error message if it encounters an unexpected rank.
  * Make it reasonably simple to add new hierarchical or non-hierarchical ranks and have the
    loader process them correctly
* Prokka annotation should be updated to `search_species` rather than `search_taxa`

### Could be done regardless of the option chosen below

* Both options below involve making changes to the loader output. Should we reload the old data?
  * From a reproducibility standpoint we shouldn't, but that also means we have to support
    the older query style if queries change
  * This might be time consuming and irritating as we'd presumably want to keep the data
    otherwise the same, including load time stamps, etc., and the loader doesn't know how to
    update an existing load
    * Might be simpler to load entirely new collections, dump the old ones, and
      [rename the new one](https://www.arangodb.com/docs/stable/http/collection-modifying.html#rename-collection)
      during a downtime
      * Note that the collection names are exposed in the API

### Option 1 - new `species_or_below` flag

The use case driving the scientific name lookup was the ability to assign a scientific name to
a genome or assembly, and as such, it didn't make sense to allow assignments to ranks above
`species`. The `strain` boolean was added to appropriate `no rank` nodes to allow them to show up
in the search.

Given that what we really want is a means of only including species-and-below ranks in the search
and `strain` is misnamed as detailed above, we will deprecate the `strain` flag and add a new
`species_or_below` flag to all nodes below the species level (including `no rank` and `clade`
nodes). We will update the taxonomy_search_species_strain* queries to return any nodes with
that flag, regardless of the rank or `strain` flag.

If we choose not to reload the data, we will keep the `strain` flag in the query for
backwards compatibility (and see the Questions section below).

This allows for future proofing changes to ranks since the queries only need to look for the
`species_or_below` flag.

In summary:
* Update the 2 taxonomy_search_species_strain* queries to handle the new `species_or_below` flag
  * Add as a parameter with default `true`
  * Clearly document that strain flag is deprecated
* Update the loader to add that flag to all appropriate nodes
  * Clearly document that strain flag is deprecated

### Option 2 - alter meaning and processing of the `strain` flag

This is similar to `Option 1`, but instead of deprecating the `strain` flag we just alter the
loader to make the `strain` flag have the same semantics as the proposed `species_or_below`
flag. The pro is that the queries can remain unchanged. The con is that the `strain` flag is
extremely badly misnamed and confusing for future developers.  

If this option is chosen the strain flag will need extremely clear documentation everywhere it
is referenced.

### Recommendation

Option 1. This is the cleaner long term solution, will reduce confusion in the future,
and isn't much more work than Option 2.

## Questions:

* The scientific name lookup queries were recently modified to be non-NCBI specific. We may need
  to investigate the rank structure in Silva, RDP, and GTDB and add a new below-species boolean
  there as well. If the only species-and-below rank is `species` then no modification is needed.