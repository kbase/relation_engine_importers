import hashlib
from Bio import SeqIO

from write_import_file import write_import_file


def load_genbank(path):
    """Load a genbank file as a Biopython object."""
    with open(path, 'r') as fd:
        try:
            genbank = SeqIO.read(fd, 'genbank')
        except Exception as err:
            raise Exception(path + '\t' + str(err))
    return genbank


def generate_genome_import_files(genbank_path, output_dir):
    """
    Generate all import files for a given genbank file path to an output_dir.
    Will produce CSV files for each collection (filename = collection name)
    """
    genbank = load_genbank(genbank_path)
    write_import_file(generate_taxa(genbank), output_dir)
    write_import_file(generate_genome(genbank), output_dir)
    write_import_file(generate_genes(genbank), output_dir)


def generate_taxa(genbank):
    """Generate taxa-related documents for import."""
    # Get a list of taxon names
    organism_name = genbank.annotations['organism']
    annot = genbank.annotations
    taxa_names = [t for t in annot['taxonomy']] + [organism_name]
    # Generate the keys using a hash function on the name
    taxa_keys = [hashlib.blake2b(n.encode(), digest_size=16).hexdigest() for n in taxa_names]
    for (idx, name) in enumerate(taxa_names):
        vertex = {'_key': taxa_keys[idx], 'name': name}
        yield ('taxa', vertex)
        if idx > 0:
            edge = {'_from': 'taxa/' + taxa_keys[idx], '_to': 'taxa/' + taxa_keys[idx - 1]}
            yield ('child_of_taxon', edge)
    # Edge for taxa to genome
    edge = {'_from': _get_genome_id(genbank), '_to': 'taxa/' + taxa_keys[-1]}
    yield ('child_of_taxon', edge)


def generate_genome(genbank):
    """
    Generate an import row for the genome with a link to the organism taxon.
    """
    row = {
        '_key': genbank.id,
        'name': genbank.name,
        'description': genbank.description,
        'molecule_type': genbank.annotations.get('molecule_type', ''),
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
        row['annotation_data'][key] = val
    yield ('genomes', row)


def generate_genes(genbank):
    """
    Generate gene rows for every feature in a genbank object.
    """
    genome_id = _get_genome_id(genbank)
    for (idx, feature) in enumerate(genbank.features):
        if feature.type == 'source':
            # Skip the 'source' feature, which describes the entire genome
            continue
        row = {
            'location_start': feature.location.start,
            'location_end': feature.location.end,
            'strand': feature.strand,
            'ref': feature.ref,
            'ref_db': feature.ref_db
        }
        for (name, val) in feature.qualifiers.items():
            # For some reason, all values under .qualifiers are lists of one elem
            # We join the elems into a string just in case there are ever multiple items
            row[name] = ', '.join(val)
        if not row.get('locus_tag'):
            # No locus tag; skip this one. We can only use features with locus tags.
            continue
        row['_key'] = row['locus_tag']
        yield ('genes', row)
        # Generate the edge from gene to genome
        gene_id = 'genes/%s' % row['_key']
        edge_key = row['_key'] + ':' + genbank.id
        edge = {'_from': gene_id, '_to': genome_id, '_key': edge_key}
        yield ('gene_within_genome', edge)


def _get_genome_id(genbank):
    return 'genomes/' + genbank.id
