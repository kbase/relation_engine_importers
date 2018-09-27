import shutil
import sys
import os
import time
from Bio import SeqIO
from pyArango.connection import Connection

from download_genbank_file import download_genbank_file
from setup_collections import setup_collections


def load_genbank(path, db):
    """
    Load a genbank file as a Biopython object
    """
    print('opening genbank file.')
    print('  size is %d bytes' % os.path.getsize(path))
    with open(path, 'r') as fd:
        genbank = SeqIO.read(fd, 'genbank')
    print('  total features: %d' % len(genbank.features))
    return genbank


def import_organism(genbank, db):
    """Import the organism collection."""
    name = genbank.annotations['organism']
    print('importing organism named %s' % name)
    query = "UPSERT @doc INSERT @doc REPLACE @doc IN organism RETURN NEW"
    doc = {'name': name}
    results = db.AQLQuery(query, bindVars={'doc': doc})
    organism_id = results[0]['_id']
    print('  upserted organism %s' % organism_id)
    return organism_id


def import_taxonomy(genbank, organism_id, db):
    """Import the taxonomy tree."""
    print('importing taxonomy')
    annot = genbank.annotations
    taxons = [t for t in annot['taxonomy']]
    name_id_dict = {}
    for t in taxons:
        doc = {'name': t}
        query = 'UPSERT @doc INSERT @doc REPLACE @doc IN taxon RETURN NEW'
        results = db.AQLQuery(query, bindVars={'doc': doc})
        _id = results[0]['_id']
        name_id_dict[t] = _id
        print('  upserted taxon %s' % t)
    print('importing parent-child edges between all taxons')
    # Create a list of (parent, child) taxon pairs
    taxon_pairs = [(taxons[idx], taxons[idx + 1]) for idx in range(len(taxons) - 1)]
    for (parent, child) in taxon_pairs:
        # Check if the taxon_has_parent edge already exists
        child_id = name_id_dict[child]
        parent_id = name_id_dict[parent]
        doc = {'_from': child_id, '_to': parent_id}
        query = 'UPSERT @doc INSERT @doc REPLACE @doc IN child_of RETURN NEW'
        results = db.AQLQuery(query, bindVars={'doc': doc})
        print('  upserted edge from %s to %s' % (child, parent))
    organism_taxon_id = name_id_dict[taxons[-1]]
    doc = {'_from': organism_id, '_to': organism_taxon_id}
    query = 'UPSERT @doc INSERT @doc REPLACE @doc IN child_of RETURN NEW'
    results = db.AQLQuery(query, bindVars={'doc': doc})
    print('  upserted edge between organism and final taxon')


def import_genome(genbank, organism_id, db):
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
        'molecule_type': genbank.annotations['molecule_type'],
        'topology': genbank.annotations['topology'],
        'data_file_division': genbank.annotations['data_file_division'],
        'date': genbank.annotations['date'],
        'accessions': genbank.annotations['accessions'],
        'sequence_version': genbank.annotations['sequence_version'],
        'source': genbank.annotations['source'],
        'dbxrefs': genbank.dbxrefs,
        'organism_name': genbank.annotations['organism'],
        'taxonomy': ', '.join(genbank.annotations['taxonomy']),
        'comment': genbank.annotations['comment'],
        'annotation_data': {}
    }
    annot_data = genbank.annotations['structured_comment'].get('Genome-Annotation-Data', {})
    for (key, val) in annot_data.items():
        genome_data['annotation_data'][key] = val
    # Create or update the genome document
    print('importing genome %s' % genome_data['organism_name'])
    query = "UPSERT @match INSERT @doc REPLACE @doc IN genome RETURN NEW"
    results = db.AQLQuery(query, bindVars={'match': match_data, 'doc': genome_data})
    genome_id = results[0]['_id']
    print('  upserted genome ' + genome_id)
    edge_data = {'_from': genome_id, '_to': organism_id}
    print('importing genome->organism edge...')
    query = "UPSERT @doc INSERT @doc REPLACE @doc IN child_of RETURN NEW"
    db.AQLQuery(query, bindVars={'doc': edge_data})
    print('  upserted edge')
    return genome_id


def import_genes(genbank, genome_id, db):
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
            print('No locus_tag on', doc)
            continue
        # Update or insert based on the locus tag
        locus_tags[doc['locus_tag']] = True
        match = {'_key': doc['locus_tag']}
        doc['_key'] = doc['locus_tag']
        query = "UPSERT @match INSERT @doc REPLACE @doc IN gene RETURN NEW"
        results = db.AQLQuery(query, bindVars={'doc': doc, 'match': match})
        gene_id = results[0]['_id']
        # Upsert an edge from the gene to the genome
        doc = {'_from': gene_id, '_to': genome_id}
        query = "UPSERT @doc INSERT @doc REPLACE @doc IN child_of"
        db.AQLQuery(query, bindVars={'doc': doc})
        upsert_count += 1
    print('  upserted %d valid annotations' % upsert_count)


if __name__ == '__main__':
    start = int(time.time() * 1000)
    if len(sys.argv) <= 1:
        sys.stderr.write('Provide an accession ID (like GCF_xyz) of a genome to download.\n')
        exit(1)
    username = os.environ.get('DB_USERNAME', 'root')
    password = os.environ.get('DB_PASSWORD', 'password')
    db_name = os.environ.get('DB_NAME', '_system')
    # Connect to the database
    try:
        conn = Connection(username=username, password=password)
    except Exception as err:
        sys.stderr.write(str(err) + '\n')
        exit(1)
    finally:
        print('database connection established.')
    db = conn[db_name]
    # Call each procedure
    genbank_dir = download_genbank_file(sys.argv[1])
    vertices = ['organism', 'taxon', 'genome', 'gene']
    edges = ['child_of', 'contains']
    setup_collections(db, vertices, edges)
    for path in os.listdir(genbank_dir):
        genbank_path = os.path.join(genbank_dir, path)
        genbank = load_genbank(genbank_path, db)
        organism_id = import_organism(genbank, db)
        import_taxonomy(genbank, organism_id, db)
        genome_id = import_genome(genbank, organism_id, db)
        import_genes(genbank, genome_id, db)
        print('*' * 80)
    shutil.rmtree(genbank_dir)
    end = int(time.time() * 1000)
    print('total running time in ms: %d' % (end - start))
