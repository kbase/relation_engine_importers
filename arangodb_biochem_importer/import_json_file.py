"""
         Import data into an arangodb collection from a json file.

Usage:   python import_json_file.py [-c, --create] [-n, --collection_name <name>]  json_file

         Each line in the file should be a json record

Options:  -c, --create   overwrite existing collection if it exists
          -n, --collection_name  <name>
                         store data in specified collection, defauts to filename root

"""
import time
import os
import sys
import requests
import logging
import argparse

log_file_path = 'import_json_data.log'
logging.basicConfig(filename=log_file_path, filemode='w', level=logging.DEBUG)


def bulk_save_post(file_path, col_name, create_collection ):
    """Make a post request to the arango http api to do a bulk save with the file."""
    # Filename is something like genomes-vertex.json
    #   where 'genomes' is the collection name and 'vertex' is document type (can also be 'edge')
    if create_collection:
        overwrite = 'yes'
    else:
        overwrite = 'no'

    query_params = {
        'type': 'documents',
        'collection': col_name,
        'overwrite': overwrite,
        'onDuplicate': 'replace'
    }
    db_url = os.environ.get('DB_URL', 'http://localhost:8530')
    db_url += '/_api/import'
    user = os.environ.get('DB_USER', 'root')
    passwd = os.environ.get('DB_PASS', 'password')
    print( "db_url: ", db_url )
    print( "params: ", query_params )
    print( "auth: ", user, passwd )
    with open(file_path, 'rb') as fd:
        resp = requests.post(db_url, data=fd, params=query_params, auth=(user, passwd))
    logging.info('imported %s' % col_name)
    logging.info('import response:\t%s' % resp.text)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument( "json_file", help="JSON format file to upload" )
    parser.add_argument( "-c", "--create", action="store_true", 
                         help="create collection anew (overwrite)" )
    parser.add_argument( "-n", "--collection_name", 
                         help="store in collection name (default comes from filename)" )

    args = parser.parse_args()

    print( "file is ", args.json_file )
    print( "create ", args.create )
    print( "collection_name", args.collection_name )

    start = int(time.time() * 1000)
    
    file_name = args.json_file
    if args.collection_name:
        col_name = args.collection_name
    else:
        col_name = os.path.splitext( os.path.basename( file_name ) )[0]

    print('logging to %s' % log_file_path)
    bulk_save_post(file_name, col_name, args.create )
    end = int(time.time() * 1000)
    logging.info('total time running in ms: %s' % (end - start))
    print('..done')
