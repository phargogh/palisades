#!/bin/bash

# A sample execution script for installing palisades to a virtual environment.

env=palisades_env

virtualenv --system-site-packages $env
source $env/bin/activate
easy_install nose  # required, since it installs nosetests.

python setup.py install
