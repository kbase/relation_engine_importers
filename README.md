# Data import scripts for the Relation Engine (KBase)

Utilities for reproducible imports into the Relation Engine from various data sources.

To run these importers, you need to have the `RE_ADMIN` auth role in your environment (CI or prod).

This is an experimental utility that imports genome and biochemistry data into an ArangoDB graph.

Build status (master):
[![Build Status](https://travis-ci.org/kbase/relation_engine_importers.svg?branch=master)](https://travis-ci.org/kbase/relation_engine_importers)
[![Coverage Status](https://coveralls.io/repos/github/kbase/relation_engine_importers/badge.svg)](https://coveralls.io/github/kbase/relation_engine_importers)

## Setup

For Ubuntu (and possibly other distributions) ensure that the appropriate `python-dev` package
is installed, e.g. `sudo apt install python3.7-dev`. 

With [pipenv](https://github.com/pypa/pipenv) installed, run:

```sh
pipenv install
```

Alternatively, you can use [pyenv](https://github.com/pyenv/pyenv) to manage your python
installations.

## Running tests

To run tests:
```
$ pipenv shell
$ export PYTHONPATH=$(pwd)/src/; pytest
```

## Usage

TODO
