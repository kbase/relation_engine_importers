"""
Import data into arangodb from a directory filled with json files.

Each filename should be a collection name

Each line in the file should be a json record
"""
import time
import os
import sys
import requests
import logging

log_file_path = 'import_json_data.log'
logging.basicConfig(filename=log_file_path, filemode='w', level=logging.DEBUG)
re_api_url = os.environ['RE_API_URL']
re_token = os.environ['RE_ADMIN_TOKEN']


def bulk_save_post(file_path, col_name):
    """Make a post request to the arango http api to do a bulk save with the file."""
    # Filename is something like genomes-vertex.json
    #   where 'genomes' is the collection name and 'vertex' is document type (can also be 'edge')
    with open(file_path, 'rb') as fd:
        resp = requests.put(
            re_api_url + '/api/v1/documents',
            params={'collection': col_name, 'overwrite': True},
            data=fd, 
            headers={'authorization':re_token}
        )
    if not resp.ok:
        raise RuntimeError(resp.text)
    logging.info('imported %s' % col_name)
    logging.info('import response:\t%s' % resp.text)


def iterate_files(json_dir):
    for file_name in os.listdir(json_dir):
        file_path = os.path.join(json_dir, file_name)
        col_name = os.path.splitext(file_name)[0]
        bulk_save_post(file_path, col_name)


if __name__ == '__main__':
    start = int(time.time() * 1000)
    if len(sys.argv) < 2:
        sys.stderr.write('Pass in a directory of JSON import data files.')
        sys.exit(1)
    json_dir = sys.argv[1]
    if not os.path.isdir(json_dir):
        sys.stderr.write('%s is not a directory' % json_dir)
        sys.exit(1)
    print('logging to %s' % log_file_path)
    iterate_files(json_dir)
    end = int(time.time() * 1000)
    logging.info('total time running in ms: %s' % (end - start))
    print('..done')