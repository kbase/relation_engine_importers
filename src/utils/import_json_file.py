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
import requests
import logging
import argparse
import json
import tempfile

chunk_size = 5e8    # in bytes.   set for under 512 Mb limit imposed by ArangoDB
                    # https://www.arangodb.com/docs/stable/http/general.html

log_file_path = 'import_json_data.log'
logging.basicConfig(filename=log_file_path, filemode='w', level=logging.DEBUG)

def post_chunkfile(file_path, col_name, create_collection, n ):
    """Make a post request to the arango http api to do a bulk save with the file."""
    # Filename is something like genomes-vertex.json
    #   where 'genomes' is the collection name and 'vertex' is document type (can also be 'edge')
    if n == 0 and create_collection:
        overwrite = 'yes'
    else:
        overwrite = 'no'

    query_params = {
        'type': 'documents',
        'collection': col_name,
        'overwrite': overwrite,
        'onDuplicate': 'replace'
    }
    print( "saving chunk {0} to {1}".format( n, file_path ) )
    db_url = os.environ.get('DB_URL', 'http://localhost:8530')
    db_url += '/_api/import'
    user = os.environ.get('DB_USER', 'root')
    passwd = os.environ.get('DB_PASS', 'password')
    print("db_url: ", db_url)
    print("params: ", query_params)
    print("auth: ", user, passwd)
    with open(file_path, 'rb') as fd:
        resp = requests.post(db_url, data=fd, params=query_params, auth=(user, passwd))
    logging.info('imported %s' % col_name)
    logging.info('import response:\t%s' % resp.text)
    print("chunk done" )


def bulk_save_post(file_path, col_name, create_collection):

    # for now, buffer chunks in a temporary file

    tf = tempfile.NamedTemporaryFile( mode="w", delete=False )
    tfname = tf.name
    current_size = 0
    nchunk = 0

    with open( file_path ) as inf:
        for line in inf:
            #obj = json.loads( line )    # question: why not just go line by line here, and
            #sobj = json.dumps( obj )    # skip the whole json parsing altogether
            #osize = len( sobj ) + 1     # +1 for new line
            osize = len( line )
            if current_size + osize > chunk_size:
                #
                # flush out chunk buffer
                #
                tf.close()
                post_chunkfile( tfname, col_name, create_collection, nchunk )
                tf = open( tfname, "w" )    # I don't see any harm in reusing the same filename for next chunk
                nchunk += 1 
                current_size = 0

            tf.write( line )
            current_size += len( line )

        # end of loop - flush out any remaining chunk
        if current_size > 0:
            tf.close()
            post_chunkfile( tfname, col_name, create_collection, nchunk )
           
        # os.unlink( tfname )     # don't forget to remove the filename



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="JSON format file to upload")
    parser.add_argument("-c", "--create", action="store_true",
                        help="create collection anew (overwrite)")
    parser.add_argument("-n", "--collection_name",
                        help="store in collection name (default comes from filename)")

    args = parser.parse_args()

    print("file is ", args.json_file)
    print("create ", args.create)
    print("collection_name", args.collection_name)

    start = int(time.time() * 1000)

    file_name = args.json_file
    if args.collection_name:
        col_name = args.collection_name
    else:
        col_name = os.path.splitext(os.path.basename(file_name))[0]

    print('logging to %s' % log_file_path)
    bulk_save_post(file_name, col_name, args.create)
    end = int(time.time() * 1000)
    logging.info('total time running in ms: %s' % (end - start))
    print('..done')
