# Genbank to ArangoDB

This is an experimental utility that takes Genbank files and imports them into an ArangoDB graph.

## Usage

### Set up python

Using python 3, start a virtual environment:

```sh
$ python -m venv env
$ source env/bin/activate
```

Then install the dependencies:

```sh
pip install -r requirements.txt
```

### Run docker

With docker and docker-compose installed, run:

```sh
$ docker-compose up
```

You should be able to access `localhost:8529` in your browser and sign on with `root` and `password`. 

### Run the importer

First, convert the genbank file into a set of CSV data files:

```sh
# python import-genbank.py <path-to-genbank-file> <path-to-output-directory>
$ python genbank-to-csv.py ncbi-data/my-genome.gb
```

## The source data

Two genomes in genbank format can be found in `/ncbi-data`:
* Haloquadratum walsbyi C23
  * https://www.ncbi.nlm.nih.gov/genome/?term=txid768065[Organism:noexp]
* Haloferax volcanii DS2
  * https://www.ncbi.nlm.nih.gov/nuccore/NC_013967.1

## The data model

_Vertexes_
* taxon (name)
* organism (name)
* annotation (gene-count, etc)
* feature (fasta-index-start, fasta-index-end, translation, product, name, etc)

_Edges_
* taxon -- taxon_has_parent --> taxon
* organism -- organism_has_taxon --> taxon
* organism -- organism_has_annotation --> annotation
* annotation -- annotation_has_feature --> feature

## Resources and references

* Python + ArangoDB: https://www.arangodb.com/tutorials/tutorial-python/
