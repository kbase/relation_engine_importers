import json
import sys


_TAXA_TYPES = {
    'd': 'domain',
    'p': 'phylum',
    'c': 'class',
    'o': 'order',
    'f': 'family',
    'g': 'genus',
    's': 'species',
}

# Graph schema looks like:
# - vertex gtdb_taxon
#   - type (eg. "Domain"), name (eg. "Bacteria")
# - vertex gtdb_organism
#   - _key (accession, eg. "RS_GCF_001245025.1")
# - edge gtdb_child_of_taxon
#   - gtdb_taxon -> gtdb_taxon
#   - gtdb_organism -> gtdb_taxon


def bac_taxonomy_to_json(tsv_path):
    path = tsv_path
    release = path.strip('.tsv')
    gtdb_vertices_path = 'gtdb_taxon.json'
    gtdb_edges_path = 'gtdb_child_of_taxon.json'
    gtdb_vertices_output = open(gtdb_vertices_path, 'a')
    gtdb_edges_output = open(gtdb_edges_path, 'a')
    # Raw data input
    input_file = open(path)
    # All the file descriptors we will need to close at the end
    to_close = [gtdb_vertices_output, gtdb_edges_output, input_file]
    # For tracking taxon names we have already found
    found_taxon_names = {}  # type: dict
    try:
        for line in input_file:
            (accession, lineage) = line.split('\t')
            # Write the gtdb_organism doc
            prev_taxon_key = None
            # Iterate over taxa
            taxa = []  # type: list
            for taxon in lineage.split(';'):
                (taxon_type_abbrev, taxa_name) = taxon.split('__')
                taxa_type = _TAXA_TYPES[taxon_type_abbrev]
                taxa_name = taxa_name.strip('\n').lower()
                if taxa_type == 'species':
                    taxa_name = taxa_name.split(" ")
                else:
                    taxa_name = [taxa_name]
                taxa.append((taxon_type_abbrev, taxa_type, taxa_name))
            for (idx, (taxon_type_abbrev, taxa_type, taxa_name)) in enumerate(taxa):
                # Write the gtdb_taxon document
                if taxa_type == 'species':
                    full_name = taxon_type_abbrev + ':' + str("_".join(taxa_name))
                else:
                    full_name = taxon_type_abbrev + ':' + taxa_name[0]
                if full_name in found_taxon_names:
                    # We have already recorded this taxon
                    continue
                vertex_doc = {'_key': full_name, 'release': release, 'rank': taxa_type, 'name': taxa_name
                              }
                for idx2 in range(0, idx+1):
                    (taxon_type_abbrev, taxa_type, taxa_name) = taxa[idx2]
                    if taxa_type == 'species':
                        vertex_doc[taxa_type] = str("_".join(taxa_name))
                    else:
                        vertex_doc[taxa_type] = taxa_name[0]
                gtdb_vertices_output.write(json.dumps(vertex_doc) + '\n')
                if prev_taxon_key is None:
                    prev_root_key = full_name
                    if prev_root_key:
                        edge_doc = {
                            '_from': full_name,
                            '_to': prev_root_key
                        }
                        gtdb_edges_output.write(json.dumps(edge_doc) + '\n')
                if prev_taxon_key:
                    # Write the edge to go from child to parent
                    # _from is child and _to is parent
                    edge_doc = {
                        '_from': "gtdb_taxon/" + full_name,
                        'child_type': 't',
                        '_to': "gtdb_taxon/" + prev_taxon_key
                    }
                    gtdb_edges_output.write(json.dumps(edge_doc) + '\n')
                prev_taxon_key = full_name
                found_taxon_names[full_name] = True
            # Write the edge to go from child to parent from the refseq entry to the species
            edge_doc = {
                '_from': "gtdb_taxon/"+accession,
                'child_type': 'o',
                '_to': "gtdb_taxon/"+taxa[-1][0] + ':' + str("_".join(taxa[-1][2]))
            }
            vertex_doc = {
                '_key': accession,
                'release': release,
                'rank': 'genome',
                'name': taxa_name
            }
            gtdb_edges_output.write(json.dumps(edge_doc) + '\n')
            gtdb_vertices_output.write(json.dumps(vertex_doc) + '\n')
    finally:
        for fd in to_close:
            fd.close()


if __name__ == '__main__':
    commands = {
        'bac_taxonomy_to_json': bac_taxonomy_to_json
    }
    if len(sys.argv) != 2:
        sys.stderr.write(f'Valid options: {list(commands.keys())}')
        sys.exit(1)
    option = sys.argv[1]
    if option not in commands:
        sys.stderr.write(f'Invalid option: {option}. Valid option: {list(commands.keys())}')
        sys.exit(1)
    commands[option](sys.argv[2])
    print('-- done --')
