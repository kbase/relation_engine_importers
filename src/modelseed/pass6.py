#!/usr/bin/env python

import csv
import re
import sys

from pprint     import pprint
from rdkit.Chem import AllChem
from rdkit      import Chem
from rdkit      import DataStructs

compounds = {}

def load_compounds( filename ):
    comps = {}
    bad_count = 0
    blank_count = 0
    with open( filename ) as csv_file:
        csvr = csv.DictReader( csv_file, delimiter='\t' )
        for row in csvr:
            id, inchi = ( row['id'], row['structure'] )
            if  inchi:
                #print( "input row {0} {1}".format( id, inchi ) )
                try:
                    smarts = Chem.MolToSmarts( Chem.MolFromInchi( inchi ) )
                    comps[id] = smarts
                    #print( "output row {0} {1} {2}".format( id, inchi, smarts ) )
                except:
                    #print( "input row {0} {1}".format( id, inchi ) )
                    #print( "bizarre", sys.exc_info()[0] )
                    bad_count = bad_count + 1
            else:
                comps[id] = ""
                blank_count = blank_count + 1

    print( "# bad inputs count: {0}".format( bad_count ) )
    print( "# blank inputs count: {0}".format( blank_count ) )
    return( comps )


def comp_lookup( comp_id ):
    return( compounds.get( comp_id ) )


def load_reactions( filename ):

    rxns = {}
    diff_fps = {}
    obsolete_count = 0

    with open( filename ) as csv_file:
        csvr = csv.DictReader( csv_file, delimiter='\t' )

        # for each reaction

        for row in csvr:
            rxn_id, stoich, is_obsolete = ( row['id'], row['stoichiometry'], row['is_obsolete'] )
            if int(is_obsolete) > 0:
                obsolete_count = obsolete_count+1
                continue
            #print( "{0}  {1}".format( id, stoich) )
            if  stoich:                                  # for now, skip blank stoichiometries (if any)
                left_side_compounds = []
                right_side_compounds = []
                smarts = None

                for cstruct in stoich.split( ';' ):
                    #print( "   cstruct: {0}".format( cstruct ) )
                    n, compid, state, x, name = re.findall( r'(?:[^:"]|"(?:\\.|[^"])*")+', cstruct )
                    #print( "     {0}:    {1} {2} {3} {4}".format( cstruct, n, compid, state, name ) )
                    smarts = comp_lookup( compid )
                    if not smarts or ( smarts == ""):
                        smarts = None
                        break
                    copies = int( abs( float(n) ) ) 
                    if copies == 0:
                        copies = copies + 1
                    if  float(n) < 0:
                        for i in range( 0, copies ):
                            left_side_compounds.append( smarts )
                    else:
                        for i in range( 0, copies ):
                            right_side_compounds.append( smarts )

                if smarts != None:
                    #print( "left" )
                    #pprint( left_side_compounds )
                    #for s in left_side_compounds:
                    #    print( s )
                    #print( "right" )
                    #pprint( right_side_compounds )
                    #for s in right_side_compounds:
                    #    print( s )
                    rxn_string = ".".join( left_side_compounds  ) + ">>" + \
                                 ".".join( right_side_compounds )
                    #print( "rxn string {0}".format( rxn_string ) )
                    fingerprint = AllChem.CreateStructuralFingerprintForReaction( AllChem.ReactionFromSmarts( rxn_string ) )
                    #pprint( fingerprint )
                    #pprint( dir( fingerprint ) )
                    #pprint( fingerprint.GetNumBits() )
                    #pprint( fingerprint.ToBinary() )
                    diff_fingerprint = AllChem.CreateDifferenceFingerprintForReaction( AllChem.ReactionFromSmarts( rxn_string ) )
                    #print( "diff_fingerprint is " )
                    #pprint( diff_fingerprint )
                    #pprint( dir( diff_fingerprint ) )
                    #pprint( diff_fingerprint.GetLength() )
                    #pprint( diff_fingerprint.GetNonzeroElements() )
                    #b = diff_fingerprint.ToBinary()
                    #print( type(b) )
                    #pprint( b )
                    rxns[rxn_id] = fingerprint
                    diff_fps[rxn_id] = diff_fingerprint

    print( "# obsolete_count = {0}".format( obsolete_count ) )
                 
    return( rxns, diff_fps )

# First load compounds and convert to SMARTS and put in table

#compounds = load_compounds( "compounds.tsv" )
compounds = load_compounds( "new_compounds.tsv" )

#pprint( compounds )

# Next, load reactions, capture reaction strings and replace compound ids with SMARTS

reactions, diffs = load_reactions( "reactions.tsv" )

rxn_list = list(reactions.keys())   # list() required for python 3
num_rxns = len( rxn_list )
#num_rxns = 10000

for i in range( 0, num_rxns-1 ):
    for j in range( i+1, num_rxns ):
        rxn_a = rxn_list[i]
        rxn_b = rxn_list[j]
        print( "{0} {1} {2} {3}".format( rxn_a, rxn_b,
                                   DataStructs.FingerprintSimilarity( reactions[rxn_a], 
                                                                      reactions[rxn_b] ),
                                   DataStructs.cDataStructs.TanimotoSimilarity( diffs[rxn_a], 
                                                                                diffs[rxn_b] )
                                             ) )

