import os
from Bio import SeqIO

from write_import_file import write_import_file

_genome_vert_name = 'rxn_genome'
_gene_vert_name = 'rxn_gene'
_gene_edge_name = 'rxn_gene_within_genome'


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
    genome_path = os.path.join(output_dir, _genome_vert_name + '.json')
    write_import_file(generate_genome(genbank), genome_path)
    gene_path = os.path.join(output_dir, genbank.id, _gene_vert_name + '.json')
    write_import_file(generate_genes(genbank), gene_path)
    gene_edge_path = os.path.join(output_dir, genbank.id, _gene_edge_name + '.json')
    write_import_file(generate_gene_edges(genbank), gene_edge_path)


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
    yield row


def generate_genes(genbank):
    """
    Generate gene rows for every feature in a genbank object.
    """
    for (idx, feature) in enumerate(genbank.features):
        # Skip the 'source' feature, which describes the entire genome
        if feature.type == 'source':
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
        yield row


def generate_gene_edges(genbank):
    """Generate gene-to-genome edges for every feature in a genbank object."""
    genome_key = genbank.id
    genome_id = _genome_vert_name + '/' + genome_key
    for (idx, feature) in enumerate(genbank.features):
        # Skip the 'source' feature, which describes the entire genome
        if feature.type == 'source' or 'locus_tag' not in feature.qualifiers:
            continue
        # Generate the edge from gene to genome
        gene_key = feature.qualifiers['locus_tag'][0]
        gene_id = _gene_vert_name + '/' + gene_key
        edge_key = gene_key + '-' + genome_key
        yield {'_from': gene_id, '_to': genome_id, '_key': edge_key}
