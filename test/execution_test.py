import unittest
import imp
import os
import logging

from palisades import execution

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, 'data')
LOGGER = logging.getLogger('test')

class ExecutorTest(unittest.TestCase):
    def test_smoke_execute(self):
        module = imp.load_source('sample', os.path.join(DATA_DIR,
            'sample_scripts.py'))
        executor = execution.Executor(module, None)
        executor.start()
        executor.join()

    def test_smoke_func_name(self):
        """Verify executor can run a function not called 'execute'"""
        module = imp.load_source('sample', os.path.join(DATA_DIR,
            'sample_scripts.py'))
        executor = execution.Executor(module, None, func_name='check_the_time')
        executor.start()
        executor.join()

    def test_with_logging(self):
        module = imp.load_source('sample', os.path.join(DATA_DIR,
            'sample_scripts.py'))
        executor = execution.Executor(module, None, func_name='try_logging')
        executor.start()
        executor.join()
        LOGGER.debug('hello.  This should not appear in the log file.')
