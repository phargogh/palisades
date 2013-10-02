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

        temp_file_uri = os.path.join(DATA_DIR, 'test_log.txt')
        executor = execution.Executor(module, None, func_name='try_logging',
            log_file=temp_file_uri)
        executor.start()
        executor.join()
        LOGGER.debug('hello.  This should not appear in the log file.')

        with open(temp_file_uri) as file_obj:
            for i, line in enumerate(file_obj):
                pass
        num_lines = i + 1

        self.assertEqual(num_lines, 2)
        os.remove(temp_file_uri)
