import unittest
import imp
import os
import logging
import shutil

from palisades import execution

TEST_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TEST_DIR, 'data')
LOGGER = logging.getLogger('test')

def count_lines(file_uri):
    """Count the number of lines in a file.

        file_uri - a URI to the file on disk.

        Returns an int."""

    with open(file_uri) as file_obj:
        for i, line in enumerate(file_obj):
            pass
    num_lines = i + 1
    return num_lines

class ExecutionUtilsTest(unittest.TestCase):
    def test_locate_module_path(self):
        executeable, name = execution.locate_module('os')
        self.assertEqual(executeable.path.join('aaa', 'bbb'), 'aaa%sbbb' % os.sep)

    def test_locate_module_file(self):
        module_path = os.path.join(DATA_DIR, 'sample_scripts.py')
        executeable, name = execution.locate_module(module_path)
        self.assertEqual(executeable.return_one(), 1)

class ExecutorTest(unittest.TestCase):
    def test_smoke_execute(self):
        module = imp.load_source('sample', os.path.join(DATA_DIR,
            'sample_scripts.py'))
        executor = execution.Executor(module, {})
        executor.start()
        executor.join()

    def test_smoke_func_name(self):
        """Verify executor can run a function not called 'execute'"""
        module = imp.load_source('sample', os.path.join(DATA_DIR,
            'sample_scripts.py'))
        executor = execution.Executor(module, {}, func_name='check_the_time')
        executor.start()
        executor.join()

    def test_with_logging(self):
        """Verify only the thread-based logging is included"""
        module = imp.load_source('sample', os.path.join(DATA_DIR,
            'sample_scripts.py'))

        temp_file_uri = os.path.join(DATA_DIR, 'test_log.txt')
        executor = execution.Executor(module, {'1':1}, func_name='try_logging',
            log_file=temp_file_uri)
        executor.start()
        executor.join()

        # This logging is generated in the main thread, not the worker thread,
        # which only logs 2 lines.  The number of lines in the log file should
        # be 5 (2 from the function, 2 from printing arguments, 1 of blank
        # space).
        LOGGER.debug('hello.  This should not appear in the log file.')

        self.assertEqual(count_lines(temp_file_uri), 9)
        os.remove(temp_file_uri)

class LogManagerTest(unittest.TestCase):
    def test_creation_logfile(self):
        """Verify that logging works when we give a uri to the Manager."""
        log_file = os.path.join(DATA_DIR, 'sample_log.txt')
        manager = execution.LogManager('MainThread', log_file)
        LOGGER.debug('Log me!')
        manager.close()
        self.assertEqual(count_lines(log_file), 1)
        os.remove(log_file)

    def test_creation_no_logfile(self):
        """Verify that logging works when we don't provide a logfile uri."""
        # When we don't give the handler a URI, it creates a NullHandler
        # instance, so we don't save any of the logging messages to the log
        # file.
        manager = execution.LogManager('sample_thread_name')
        manager.close()
        self.assertEqual(manager.logfile_handler.__class__,
            logging.NullHandler)


    def test_print_args_dict(self):
        """Verify that argument printing is correct."""
        log_file = os.path.join(DATA_DIR, 'sample_log.txt')
        if os.path.exists(log_file):
            os.remove(log_file)
        self.assertEqual(os.path.exists(log_file), False)
        manager = execution.LogManager('MainThread', log_file)

        args = {}
        manager.print_args(args)
        self.assertEqual(count_lines(log_file), 4)
        os.remove(log_file)

    def test_print_args_dict_full(self):
        """Verify that argument printing happens correctly with an args dict."""
        log_file_uri = os.path.join(DATA_DIR, 'sample_log.txt')
        if os.path.exists(log_file_uri):
            os.remove(log_file_uri)
        self.assertEqual(os.path.exists(log_file_uri), False)
        manager = execution.LogManager('MainThread', log_file_uri)

        args = {
            'a': 'aaa',
            'b': 'bbb',
            'cdefg': u'qwerty',
            'hello': 12345,
            'list': range(4)
        }
        manager.print_args(args)
        self.assertEqual(count_lines(log_file_uri), 8)

        regression_file_uri = os.path.join(DATA_DIR, 'execution',
            'arguments_only.txt')
        regression_file = open(regression_file_uri)
        log_file = open(log_file_uri)

        # Loop through all the lines in both files, assert they're equal.
        lines = lambda f: [l for l in f]
        for index, (log_msg, reg_msg) in enumerate(zip(lines(log_file), lines(regression_file))):
            if index == 0:
                continue  # skip a logging line with the date/time
            self.assertEqual(log_msg, reg_msg)

        os.remove(log_file_uri)

class PythonRunnerTest(unittest.TestCase):
    def test_smoke(self):
        module_path = os.path.join(DATA_DIR, 'sample_scripts.py')
        new_workspace = os.path.join(DATA_DIR, 'test_workspace')
        runner = execution.PythonRunner(module_path, {'workspace_dir':
            new_workspace})
        runner.start()
        runner.executor.join()
        shutil.rmtree(new_workspace)

    #TODO: Finish testing the PythonRunner class.
