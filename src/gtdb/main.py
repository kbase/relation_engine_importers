import json
import time
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


def bac_taxonomy_to_json():
    path = 'bac120_taxonomy_r89.tsv'
    timestamp = str(int(time.time() * 1000))
    gtdb_taxon_path = f'gtdb_taxon-{timestamp}.json'
    gtdb_organism_path = f'gtdb_organism-{timestamp}.json'
    gtdb_child_of_taxon_path = f'gtdb_child_of_taxon-{timestamp}.json'
    gtdb_taxon_output = open(gtdb_taxon_path, 'a')
    gtdb_organism_output = open(gtdb_organism_path, 'a')
    gtdb_child_of_taxon_output = open(gtdb_child_of_taxon_path, 'a')
    # Raw data input
    input_file = open(path)
    # All the file descriptors we will need to close at the end
    to_close = [gtdb_taxon_output, gtdb_organism_output, gtdb_child_of_taxon_output, input_file]
    # For tracking taxon names we have already found
    found_taxon_names = {}  # type: dict
    try:
        for line in input_file:
            (accession, lineage) = line.split('\t')
            # Write the gtdb_organism doc
            refseq_doc = {'_key': accession}
            gtdb_organism_output.write(json.dumps(refseq_doc) + '\n')
            prev_taxon_key = None
            # Iterate over taxa
            taxa = []  # type: list
            for taxon in lineage.split(';'):
                (short_type, name) = taxon.split('__')
                type_name = _TAXA_TYPES[short_type]
                name = name.strip('\n').lower()
                if type_name == 'species': 
                    name = name.split(" ")
                if name:
                    taxa.append((short_type, type_name, name))
            for (idx, (short_type, type_name, name)) in enumerate(taxa):
                # Write the gtdb_taxon document
                if type_name == 'species': 
                    full_name = short_type + ':' + str(" ".join(name))
                else: 
                    full_name = short_type + ':' + name
                if full_name in found_taxon_names:
                    # We have already recorded this taxon
                    continue
                taxon_doc = {'_key': full_name, 'type': type_name, 'name': name
                            }
                for idx2 in range(0, idx+1):
                    (short_type, type_name, name) = taxa[idx2]
                    taxon_doc[type_name] = name
                gtdb_taxon_output.write(json.dumps(taxon_doc) + '\n')
                if prev_taxon_key:
                    # Write the edge to go from child to parent
                    # _from is child and _to is parent
                    child_doc = {
                        '_from': full_name,
                        '_to': prev_taxon_key
                    }
                    gtdb_child_of_taxon_output.write(json.dumps(child_doc) + '\n')
                prev_taxon_key = full_name
                found_taxon_names[full_name] = True
            # Write the edge to go from child to parent from the refseq entry to the species
            child_doc = {
                '_from': accession,
                '_to': taxa[-1][0] + ':' + str(" ".join(taxa[-1][2]))
            }
            gtdb_child_of_taxon_output.write(json.dumps(child_doc) + '\n')
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
    commands[option]()
    print('-- done --')
