#!/usr/bin/env python

import hashlib
import json
import sys
import os

rxn_table = {}
gene_table = {}

def  make_gene_complex_key( gene ):

    return( hashlib.blake2b(str( [gene,"KEGG"] ).encode(), digest_size=16).hexdigest() )


def  read_kegg_mapping( file ):

    with open( file ) as f:
        next( f )            # skip header
        for line in f:
            n, rxn, assignments, n_assign = line.strip().split(',')
            
            if not rxn_table.get( rxn ):
                rxn_table[rxn] = []
            for a in assignments.split( ';' ):
                genome, gene = a.split( ':' )
                rxn_table[rxn] = rxn_table[rxn] + [ [genome,gene] ]
                if not gene_table.get( gene ):
                    gene_table[gene] = make_gene_complex_key( gene )

def  output_json_rxn_gene_complex( outfile ):

    with open( outfile, 'w' ) as outf:
        for gene in gene_table:
            outf.write( json.dumps( { 'genes': [ gene ], 'source': 'KEGG', '_key': gene_table[gene] } ) + "\n")
        print( '{0} written'.format( outfile ) )

def output_json_rxn_reaction_within_complex( outfile ):

    with open( outfile, 'w' ) as outf:
        for rxn in rxn_table:
            for gg in rxn_table.get( rxn ):
                outf.write( json.dumps( { '_from': 'rxn_reaction/' + rxn, 
                                          '_to': 'rxn_gene_complex/' + gene_table.get( gg[1] ) 
                                        } ) + "\n" )
        print( '{0} written'.format( outfile ) )

def output_json_rxn_gene_within_complex( outfile ):

    with open( outfile, 'w' ) as outf:
        for gene in gene_table:
            outf.write( json.dumps( { '_from': 'ncbi_gene/' + gene, 
                                      '_to': 'rxn_gene_complex/' + gene_table[gene] 
                                    } ) + "\n" )
        print( '{0} written'.format( outfile ) )


                                ########
                                # Main #
                                ########

kegg_mapping_file = sys.argv[1]
output_dir = sys.argv[2]

read_kegg_mapping( kegg_mapping_file )

#for r in rxn_table:
#    print( "{0}: {1}".format( r, len( rxn_table[r] ) ) )

#for g in gene_table:
#    print( "{0}: {1}".format( g, gene_table[g] ) )

output_json_rxn_gene_complex( os.path.join( output_dir, 'kegg_rxn_gene_complex.json' ) )
output_json_rxn_reaction_within_complex( os.path.join( output_dir, 'kegg_rxn_reaction_within_complex.json' ) )
output_json_rxn_gene_within_complex( os.path.join( output_dir, 'kegg_rxn_gene_within_complex.json' ) )


