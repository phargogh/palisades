"""This is a python module containing sample functions for testing the Executor
classes."""

import time
import datetime

def execute(args):
    for i in range(3):
        time.sleep(1)

def check_the_time(args):
    print datetime.datetime.now()
