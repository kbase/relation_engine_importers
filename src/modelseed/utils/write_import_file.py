import os
import json


def write_import_file(row_gen, output_path):
    """
    Write out an importable file of JSON import data
    Args:
      generator - yields csv rows to import
      output_path - csv file path to write to
      headers - list of header names
    Returns a dictionary of counts for how many rows generated for each collection
        (keys are collection names, values are counts)
    """
    # Assure that the directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Iterate over every generate set of data, convert it to JSON, and append
    # it to the file
    with open(output_path, 'a') as fd:
        for data in row_gen:
            json_data = json.dumps(data)
            fd.write(json_data + '\n')


def write_multiple_import_files(row_gen, outputs):
    """
    Write out multiple json import paths
    The generator should yield (path, data)
    `outputs` should be a dictionary where
        keys are collection names
        values are output file paths
    """
    # Assure that the directories exist
    # Iterate over every generate set of data, convert it to JSON, and append it to the file
    fds = {}
    for (name, path) in outputs.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fds[name] = open(path, 'a')  # append mode
    for (name, data) in row_gen:
        json_data = json.dumps(data)
        fds[name].write(json_data + '\n')
    for (name, fd) in fds.items():
        fd.close()
