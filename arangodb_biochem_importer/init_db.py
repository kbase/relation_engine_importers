import sys
import os
from pyArango.connection import Connection


def init_db():
    """
    Initialize a connection instance to a running Arango database.
    Optional environment variables that are used here:
        DB_USERNAME
        DB_PASSWORD
        DB_NAME
        DB_URL
    All of the above have fallback values for a local test setup.
    """
    username = os.environ.get('DB_USERNAME', 'root')
    password = os.environ.get('DB_PASSWORD', 'password')
    db_name = os.environ.get('DB_NAME', '_system')
    db_url = os.environ.get('DB_URL', 'http://localhost:8529')
    # Connect to the database
    try:
        conn = Connection(username=username, password=password, arangoURL=db_url)
    except Exception as err:
        sys.stderr.write(str(err) + '\n')
        exit(1)
    finally:
        print('database connection established.')
    return conn[db_name]
