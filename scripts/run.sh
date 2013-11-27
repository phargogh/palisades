#!/bin/bash

# A sample execution script for installing palisades to a virtual environment.

env=palisades_env

virtualenv --system-site-packages $env
source $env/bin/activate

python setup.py install
