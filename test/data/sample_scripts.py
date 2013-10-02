"""This is a python module containing sample functions for testing the Executor
classes."""

import time
import datetime
import logging

logging.basicConfig(format='%(asctime)s %(name)-18s %(threadName)-10s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('sample_scripts')

def execute(args):
    for i in range(3):
        time.sleep(1)

def check_the_time(args):
    print datetime.datetime.now()

def try_logging(args):
    LOGGER.debug('Starting the function')
    LOGGER.debug('Finishing the function')
