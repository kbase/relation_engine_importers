"""
Utilities for importing genbank files into an ArangoDB graph.
"""
import time
import os
import sys
from Bio import SeqIO
from pyArango.connection import Connection


def setup_collections(db):
    """
    Create all the required database vertexes and edges if they don't exist.
    """
    vertex_names = ['organism', 'taxon', 'annotation', 'feature']
    print('required vertexes: ' + ', '.join(vertex_names))
    for name in vertex_names:
        if db.hasCollection(name):
            print('has "%s" vertex' % name)
        else:
            print('does not have "%s" vertex' % name)
            db.createCollection(name=name)
            print('...created.')
    edge_names = ['organism_has_taxon', 'taxon_has_parent', 'organism_has_annotation', 'annotation_has_feature']
    print('required edges: ' + ', '.join(edge_names))
    for name in edge_names:
        if db.hasCollection(name):
            print('has "%s" edge' % name)
        else:
            print('does not have "%s" edge' % name)
            db.createCollection(name=name, className='Edges')
            print('...created.')
    print('done setting up collections.')


def open_genbank(path, db):
    print('opening genbank file.')
    print('size is %d bytes' % os.path.getsize(path))
    with open(path, 'r') as fd:
        genbank = SeqIO.read(fd, 'genbank')
    print('total features: %d' % len(genbank.features))
    return genbank


def import_organism(genbank, db):
    """Import the organism collection."""
    name = genbank.annotations['organism']
    print('importing organism named %s' % name)
    query = "UPSERT @doc INSERT @doc REPLACE @doc IN organism RETURN NEW"
    doc = {'name': name}
    results = db.AQLQuery(query, bindVars={'doc': doc})
    _id = results[0]['_id']
    print('upserted organism with id %s' % _id)
    return {'organism': _id}


def import_taxonomy(genbank, created_docs, db):
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
        print('upserted %s into the db' % t)
    print('upserting parent-child edges between all taxons')
    # Create a list of (parent, child) taxon pairs
    taxon_pairs = [(taxons[idx], taxons[idx + 1]) for idx in range(len(taxons) - 1)]
    for (parent, child) in taxon_pairs:
        # Check if the taxon_has_parent edge already exists
        child_id = name_id_dict[child]
        parent_id = name_id_dict[parent]
        doc = {'_from': child_id, '_to': parent_id}
        query = 'UPSERT @doc INSERT @doc REPLACE @doc IN taxon_has_parent RETURN NEW'
        results = db.AQLQuery(query, bindVars={'doc': doc})
        print('upserted edge from %s to %s' % (child, parent))
    print('upserting edge between organism and final taxon')
    organism_taxon_id = name_id_dict[taxons[-1]]
    doc = {'_from': created_docs['organism'], '_to': organism_taxon_id}
    query = 'UPSERT @doc INSERT @doc REPLACE @doc IN organism_has_taxon RETURN NEW'
    results = db.AQLQuery(query, bindVars={'doc': doc})
    print('upserted %s', results[0]['_id'])
    return created_docs


def import_annotation(genbank, created_docs, db):
    """Import annotation info."""
    print('upserting annotation')
    # Check if the organism->annotation
    doc = {
        'name': genbank.name,
        '_key': genbank.id,
        'date': genbank.annotations['date']
    }
    search = {'_key': genbank.id}
    query = 'UPSERT @search INSERT @doc REPLACE @doc IN annotation RETURN NEW'
    results = db.AQLQuery(query, bindVars={'doc': doc, 'search': search})
    _id = results[0]['_id']
    created_docs['annotation'] = _id
    print('upserted %s' % _id)
    print('upserting edge between annotation and organism')
    # Check if the annotation->organism edge exists
    doc = {'_from': created_docs['organism'], '_to': _id}
    query = 'UPSERT @doc INSERT @doc REPLACE @doc IN organism_has_annotation RETURN NEW'
    results = db.AQLQuery(query, bindVars={'doc': doc})
    print('upserted %s' % results[0]['_id'])
    return created_docs


def import_annotation_feature(genbank, created_docs, db):
    """Import annotation features."""
    print('importing %d features...' % len(genbank.features))
    upsert_count = 0
    for feature in genbank.features:
        if feature.type not in ['gene', 'CDS', 'tRNA', 'rRNA', 'ncRNA']:
            print('  (not importing feature type "%s")' % feature.type)
            continue
        doc = {
            'location_start': feature.location.start,
            'location_end': feature.location.end,
            'type': feature.type
        }
        for (name, val) in feature.qualifiers.items():
            doc[name] = val[0]
        locus_tag = feature.qualifiers['locus_tag'][0]
        search = {'locus_tag': locus_tag}
        query = "UPSERT @search INSERT @doc REPLACE @doc IN feature"
        db.AQLQuery(query, bindVars={'doc': doc, 'search': search})
        upsert_count += 1
    print('created/replaced %d genes' % upsert_count)
    return created_docs


if __name__ == '__main__':
    start = int(time.time() * 1000)
    if len(sys.argv) < 2:
        print("Error: pass the path of a genbank file as the first argument")
        print("Example: python import-genbank.py ncbi-data/my-genome.gb")
        exit(1)
    # Get the genbank file path
    path = sys.argv[1]
    if not os.path.exists(path):
        print('file does not exist: %s' % path)
        exit(1)
    # Connect to the database
    try:
        conn = Connection(username='root', password='password')
    except Exception as err:
        print(str(err))
        exit(1)
    finally:
        print('database connection established.')
    db = conn['_system']  # Can be updated to something more descriptive later
    # Call each procedure
    setup_collections(db)
    print('-' * 40)
    genbank = open_genbank(path, db)
    print('-' * 40)
    created_docs = import_organism(genbank, db)
    print('-' * 40)
    created_docs = import_taxonomy(genbank, created_docs, db)
    print('-' * 40)
    created_docs = import_annotation(genbank, created_docs, db)
    print('-' * 40)
    created_docs = import_annotation_feature(genbank, created_docs, db)
    print('-' * 40)
    print('all done! play with the graph at: http://localhost:8529')
    end = int(time.time() * 1000)
    print('total running time in ms: %d' % (end - start))
