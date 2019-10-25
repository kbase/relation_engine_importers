#!/bin/sh

# Run this script in a virtual environment
# Run this script from the repo's root directory.

set -e

export PYTHONPATH=$(pwd):$(pwd)/src/
flake8 . &&
pytest
