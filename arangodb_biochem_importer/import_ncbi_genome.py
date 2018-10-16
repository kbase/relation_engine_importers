import os
from Bio import SeqIO

from init_db import init_db
from setup_collections import setup_collections

db = init_db()


def setup():
    """Setup the database connection and collections; returns the connection."""
    vertices = ['organisms', 'taxa', 'genomes', 'genes']
    edges = ['child_of_taxon', 'genome_has_gene', 'organism_has_genome']
    setup_collections(db, vertices, edges)
    return db


def load_genbank(path):
    """Load a genbank file as a Biopython object."""
    print('opening genbank file.')
    print('  size is %d bytes' % os.path.getsize(path))
    with open(path, 'r') as fd:
        genbank = SeqIO.read(fd, 'genbank')
    print('  total features: %d' % len(genbank.features))
    return genbank


def import_organism(genbank):
    """Import the organism collection."""
    name = genbank.annotations['organism']
    print('importing organism named %s' % name)
    query = "UPSERT @doc INSERT @doc REPLACE @doc IN organisms RETURN NEW"
    doc = {'name': name}
    results = db.AQLQuery(query, bindVars={'doc': doc})
    organism_id = results[0]['_id']
    print('  upserted organism %s' % organism_id)
    return organism_id


def import_taxonomy(genbank, organism_id):
    """Import the taxonomy tree."""
    print('importing taxonomy')
    annot = genbank.annotations
    taxa = [t for t in annot['taxonomy']]
    name_id_dict = {}
    for t in taxa:
        doc = {'name': t}
        query = 'UPSERT @doc INSERT @doc REPLACE @doc IN taxa RETURN NEW'
        results = db.AQLQuery(query, bindVars={'doc': doc})
        _id = results[0]['_id']
        name_id_dict[t] = _id
        print('  upserted taxon %s' % t)
    print('importing parent-child edges between all taxa')
    # Create a list of (parent, child) taxon pairs
    taxon_pairs = [(taxa[idx], taxa[idx + 1]) for idx in range(len(taxa) - 1)]
    for (parent, child) in taxon_pairs:
        # Check if the taxon_has_parent edge already exists
        child_id = name_id_dict[child]
        parent_id = name_id_dict[parent]
        doc = {'_from': child_id, '_to': parent_id}
        query = 'UPSERT @doc INSERT @doc REPLACE @doc IN child_of_taxon RETURN NEW'
        results = db.AQLQuery(query, bindVars={'doc': doc})
        print('  upserted edge from %s to %s' % (child, parent))
    organism_taxon_id = name_id_dict[taxa[-1]]
    doc = {'_from': organism_id, '_to': organism_taxon_id}
    query = 'UPSERT @doc INSERT @doc REPLACE @doc IN child_of_taxon RETURN NEW'
    results = db.AQLQuery(query, bindVars={'doc': doc})
    print('  upserted edge between organism and final taxon')


def import_genome_document(genbank, organism_id):
    """
    Import a single `genome` doc with all the data from the genbank
    Insert a child_of edge between the genome and organism
    """
    # Data for matching identical, existing records to update
    match_data = {'_key': genbank.id}
    genome_data = {
        '_key': genbank.id,
        'name': genbank.name,
        'description': genbank.description,
        'molecule_type': genbank.annotations('molecule_type', ''),
        'topology': genbank.annotations.get('topology', ''),
        'data_file_division': genbank.annotations.get('data_file_division', ''),
        'date': genbank.annotations.get('date', ''),
        'accessions': genbank.annotations.get('accessions', []),
        'sequence_version': genbank.annotations.get('sequence_version', ''),
        'source': genbank.annotations.get('source', ''),
        'dbxrefs': genbank.dbxrefs,
        'organism_name': genbank.annotations.get('organism', ''),
        'taxonomy': ', '.join(genbank.annotations.get('taxonomy', '')),
        'comment': genbank.annotations.get('comment', ''),
        'annotation_data': {}
    }
    annot_data = genbank.annotations.get('structured_comment', {}).get('Genome-Annotation-Data', {})
    for (key, val) in annot_data.items():
        genome_data['annotation_data'][key] = val
    # Create or update the genome document
    print('importing genome %s' % genome_data['organism_name'])
    query = "UPSERT @match INSERT @doc REPLACE @doc IN genomes RETURN NEW"
    results = db.AQLQuery(query, bindVars={'match': match_data, 'doc': genome_data})
    genome_id = results[0]['_id']
    print('  upserted genome ' + genome_id)
    edge_data = {'_from': organism_id, '_to': genome_id}
    print('importing genome to organism edge...')
    query = "UPSERT @doc INSERT @doc REPLACE @doc IN organism_has_genome RETURN NEW"
    db.AQLQuery(query, bindVars={'doc': edge_data})
    print('  upserted edge')
    return genome_id


def import_genes(genbank, genome_id):
    """Import gene data from the genbank file."""
    print('importing %d features from %s' % (len(genbank.features), genome_id))
    upsert_count = 0
    locus_tags = {}  # type: dict
    for feature in genbank.features:
        if feature.type == 'source':
            continue
        doc = {
            'location_start': feature.location.start,
            'location_end': feature.location.end,
            'strand': feature.strand,
            'ref': feature.ref,
            'ref_db': feature.ref_db
        }
        for (name, val) in feature.qualifiers.items():
            # For some reason, all values under .qualifiers are lists of one elem
            doc[name] = ', '.join(val)
        if not doc.get('locus_tag'):
            # No locus tag; skip this one
            continue
        # Update or insert based on the locus tag
        locus_tags[doc['locus_tag']] = True
        match = {'_key': doc['locus_tag']}
        doc['_key'] = doc['locus_tag']
        query = "UPSERT @match INSERT @doc REPLACE @doc IN genes RETURN NEW"
        results = db.AQLQuery(query, bindVars={'doc': doc, 'match': match})
        gene_id = results[0]['_id']
        # Upsert an edge from the gene to the genome
        doc = {'_from': genome_id, '_to': gene_id}
        query = "UPSERT @doc INSERT @doc REPLACE @doc IN genome_has_gene"
        db.AQLQuery(query, bindVars={'doc': doc})
        upsert_count += 1
    # TODO do a bulk save here
    print('  upserted %d valid annotations' % upsert_count)


def import_genomes(genbank_dir):
    """Download all the genome data for a given NCBI ID."""
    # For every genbank file, create all the vertices and edges
    for path in os.listdir(genbank_dir):
        genbank_path = os.path.join(genbank_dir, path)
        # genbank is a biopython SeqRecord object
        genbank = load_genbank(genbank_path)
        organism_id = import_organism(genbank)
        import_taxonomy(genbank, organism_id)
        genome_id = import_genome_document(genbank, organism_id)
        import_genes(genbank, genome_id)
