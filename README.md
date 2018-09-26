# Genbank to ArangoDB

This is an experimental utility that takes Genbank files and imports them into an ArangoDB graph.

## Usage

Have a running ArangoDB server on `localhost:8529`

### Importing a genome

You need the NCBI identifier for the genome, such as `GCF_000018105.1`.

```sh
$ python import_genome.py GCF_000018105.1
```

This will pull the genome from NCBI and import the following vertices and edges:

* genomes
* genes
* genomes -> *contains* -> genes

### Importing chemical compounds

Provide a `.tsv` of compound data with the following columns:

```csv
id,name,formula,charge,inchikey,smiles,deltag,kegg,id,ms,id
```

Run the import using:

```sh
$ python import_compounds.py GCF_000021285.1.mdl-compounds.tsv
```

This will import vertices in the `compounds` collection and no edges.

### Importing reactions

Provide a `.tsv` of reaction data with the following columns:

```csv
id,direction,compartment,gpr,name,enzyme,deltag,reference,equation,definition,ms id,bigg id,kegg id,kegg pathways,metacyc pathways
```

Run the import using:

```sh
$ python import_reactions.py GCF_000021285.1.mdl-reactions.tsv
```

This creates the following nodes/edges:

* reactions
* reaction_components
* reaction_components -> *contains* -> genes
* reaction_components -> *produces* -> reaction

### Importing reaction similarities

Provide a `.tsv` with these headers:

```csv
reactionID1,reactionID2,distance
```

This will import `similarTo` edges for each pair of reactions

### Genbank file importer

Run it with:

```sh
$ python import_genbank.py ncbi-data/my-genome.gb
```

