import threading
import logging
import os
import imp
import datetime
import sys
import time
import importlib
import contextlib
import tempfile
import pprint
import traceback

from palisades.utils import Communicator
from palisades.utils import RepeatingTimer

LOGGER = logging.getLogger('palisades.execution')


@contextlib.contextmanager
def patch_tempdir(tempdir_path):
    """Manage a context with tempfiles saved to a defined directory.

    When inside of this activated context, the environment variables
    ``TMP``, ``TEMP``, and ``TEMPDIR``, as well as ``tempfile.tempdir``, will
    all be set to the ``tempdir_path`` parameter.  These values will be
    restored to their original states when the context manager exits.

    Parameters:
        tempdir_path (string): The path to the new folder where tempfiles
            should be saved.  See python's ``tempfile`` documentation for
            details.
    """
    old_env_values = {}
    for tmp_variable in ['TMP', 'TEMP', 'TEMPDIR']:
        LOGGER.debug('Setting $%s=%s', tmp_variable, tempdir_path)
        try:
            current_value = os.environ[tmp_variable]
        except KeyError:
            current_value = None
        old_env_values[tmp_variable] = current_value

        os.environ[tmp_variable] = tempdir_path

    old_tempdir = tempfile.tempdir
    tempfile.tempdir = tempdir_path

    yield

    tempfile.tempdir = old_tempdir
    for env_varname, old_value in old_env_values.iteritems():
        LOGGER.debug('Restoring former value of $%s=%s', env_varname,
                     old_value)
        if not old_value:
            del os.environ[env_varname]
        else:
            os.environ[env_varname] = old_value


class ThreadFilter(logging.Filter):
    """When used, this filters out log messages that were recorded from other
    threads.  This is especially useful if we have logging coming from several
    concurrent threads.

    Arguments passed to the constructor:
        thread_name - the name of the thread to identify.  If the record was
            reported from this thread name, it will be passed on.

    """
    def __init__(self, thread_name):
        logging.Filter.__init__(self)
        self.thread_name = thread_name

    def filter(self, record):
        if record.threadName == self.thread_name:
            return True
        return False


class PalisadesFilter(logging.Filter):
    def filter(self, record):
        if record.name.startswith('palisades'):
            return False
        return True


class ErrorQueueFilter(logging.Filter):
    """When used, this filters for log messages that have a user-defined log
    level or greated and tracks matching messages.
    This is useful for accumulating log messages for the end of a script run.

    Arguments passed to the constructor:
        threshold - an int.  Defaults to logging.WARNING (30)
    """
    def __init__(self, threshold=logging.WARNING):
        logging.Filter.__init__(self)
        self.threshold = threshold
        self._queue = []

    def filter(self, record):
        if record.levelno >= self.threshold:
            self._queue.append(record)
        return True

    def get_errors(self):
        return self._queue


class TimedProgressLoggingFilter:
    """Filter log messages based on the time of the previous log message.

    All messages are filtered in this way, regardless of priority.

    This class also functions as a context manager.
    """
    def __init__(self, interval):
        self.interval = interval
        self.last_time = time.time()

    def filter(self, record):
        if not hasattr(record, 'progress'):
            return True

        current_time = time.time()
        if current_time - self.last_time > self.interval:
            self.last_time = time.time()
            return True
        return False


def locate_module(module):
    """Locate and import the requested module.

        module - a python string, either in python's package.subpackage.module
            notation or a URI on disk.

        Returns a tuple of (executeable module, module name)"""

    LOGGER.debug('Trying to import %s', module)
    try:
        importlib.import_module(module)
    except ImportError:
        LOGGER.debug('Importlib import failed: %s', module)

    if module in sys.modules:
        model = sys.modules[module]
        model_name = model.__name__
        LOGGER.debug('Found %s in sys.modules', module)
    elif os.path.isfile(module):
        model = imp.load_source('model', module)
        # Model name is name of module file, minus the extension
        model_name = os.path.splitext(os.path.basename(module))[0]
        LOGGER.debug('Loading %s from %s', model_name, model)
    else:
        LOGGER.debug('PATH: %s', sys.path)
        model_name = os.path.splitext(os.path.basename(module))[0]
        try:
            # __import__ only imports the top-level package if a multi-level
            # package string is provided (e.g. in package.subpackage.module,
            # the resulting import will be for package only).
            # therefore, we need to import each level sequentially
            # TODO: test this
            LOGGER.debug('Direct import failed, trying to split module')
            modules = module.split('.')
            model = __import__(modules[0])  # import base level

            if len(modules) > 1:  # if more than one level, get desired module.
                for subpackage in modules[1:]:
                    model = __import__(subpackage)

            model_name = model.__name__
            LOGGER.debug('Imported directly from the existing PATH')
        except ImportError:
            module_list = module.split('.')
            try:
                LOGGER.debug('Trying IUI-style import')
                model = _iui_style_import(module_list)
            except ImportError:
                LOGGER.debug('Trying to load module from PATH')
                model = _get_module_from_path(module_list)
                model_name = module_list[-1]  # model name is last entry in list
        LOGGER.debug('Loading %s from PATH', model_name)
    LOGGER.debug('Model successfully loaded from %s', model.__file__)
    return (model, model_name)


def _iui_style_import(module_list, path=None):
    """Search for and return an executable module object as long as the target
        module is within the pythonpath.  This method recursively uses the
        find_module and load_module functions of the python imp module to
        locate the target module by its heirarchical module name.

        module_list - a python list of strings, where each element is the name
            of a contained module.  For example, os.path would be represented
            here as ['os', 'path'].
        path=None - the base path to search.  If None, the pythonpath will be
            used.

        returns an executeable python module object if it can be found.
        Returns None if not."""

    current_name = module_list[0]
    module_info = imp.find_module(current_name, path)
    imported_module = imp.load_module(current_name, *module_info)

    if len(module_list) > 1:
        return _iui_style_import(module_list[1:], imported_module.__path__)
    else:
        return imported_module


def _get_module_from_path(module_list, path=None):
    """Search for and return an executable module object as long as the target
        module is within the pythonpath.  This method recursively uses the
        find_module and load_module functions of the python imp module to
        locate the target module by its heirarchical module name.

        module_list - a python list of strings, where each element is the name
            of a contained module.  For example, os.path would be represented
            here as ['os', 'path'].
        path=None - the base path to search.  If None, the pythonpath will be
            used.

        returns an executeable python module object if it can be found.
        Returns None if not."""

    LOGGER.debug('Importing module list %s.', module_list)
    if path is not None:
        LOGGER.debug('Adding to path %s', path)
        sys.path += path  # path is expected to be a list of URIs.
        LOGGER.debug(sys.path)

    current_name = module_list[0]
    module_info = imp.find_module(current_name, path)
    imported_module = imp.load_module(current_name, *module_info)

    if len(module_list) > 1:
        try:
            package_path = imported_module.__path__
        except AttributeError:
            # When the imported_module isn't a package
            package_path = os.path.dirname(imported_module.__file__)

        return _get_module_from_path(module_list[1:], package_path)
    else:
        return imported_module


# TODO: Need ability to run some things pre-run:
#  * redirect temp folder to workspace
#  * make the workspace
#  * execute another script (such as the InVEST logger)
class PythonRunner():
    """Wrapper object for the executor class
        * Loads the target module
        * Creates the output workspace
        * Runs the executor
        * contains communicator event objects that other functions can register
          with.
    """
    def __init__(self, module_string, args, func_name='execute'):
        """Initialization function for the PythonRunner class.

            module_string - a python string.  Must either be a URI to a python
                source file or a python path string in the form
                'package.subpackage.module' that can be loaded from the
                pythonpath.
            args - a python dictionary of argumnents to be passed to the
                function specified.
            func_name='execute' - the function to be called on the loaded
                module.  Defaults to 'execute' for IUI compatibility."""

        assert isinstance(args, dict), ('Args must be a dict, '
            '%s (%s) found instead' % (args, type(args)))

        module, module_name = locate_module(module_string)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d--%H_%M_%S")
        filename = '%s-log-%s.txt' % (module_name, timestamp)

        tempdir = os.path.join(args['workspace_dir'], 'tmp')
        for path in [args['workspace_dir'], tempdir]:
            try:
                os.makedirs(tempdir)
            except OSError:
                # folder already exists, so no need to do anything else.
                pass

        log_file_uri = os.path.join(args['workspace_dir'], filename)
        self.executor = Executor(module, args, func_name, log_file_uri, tempdir=tempdir)
        self._checker = RepeatingTimer(0.1, self._check_executor)
        self.args = args

        self.started = Communicator()
        self.finished = Communicator()
        self.failed = None
        self.traceback = None

    def start(self):
        """Start the execution of the thread and the internal status checker.
        Emits the started signal.

        Returns nothing."""

        self.failed = None
        self.traceback = None

        self.executor.start()
        LOGGER.debug('Started executor thread')

        self._checker.start()
        LOGGER.debug('Started checker thread')

        self.started.emit(thread_name=self.executor.name,
                          thread_args=self.args)

    def is_finished(self):
        """Check whether the current executor thread is active.
        Returns a boolean."""
        if self.executor is None:
            return True
        else:
            return not self.executor.is_alive()

    def _check_executor(self):
        """Check if the executor thread has finished.  If it has finished, emit
        the finished signal.  Returns nothing."""

        if not self.executor.is_alive():
            self._checker.cancel()
            self.failed = self.executor.failed
            self.traceback = self.executor.traceback
            self.finished.emit(thread_name=self.executor.name,
                               thread_failed=self.executor.failed,
                               thread_traceback=self.executor.traceback)
            del self.executor
            self.executor = None


class LogManager():
    LOG_FMT = "%(asctime)s %(name)-18s %(levelname)-8s %(message)s"
    DATE_FMT = "%m/%d/%Y %H:%M:%S "

    def __init__(self, thread_name, log_uri=None):
        """Initialization function for the LogManager.

            thread_name - A string. Log messsages will only be recorded from
                this thread.
            log_uri=None - a URI or None.  If a URI is given, all logging will
                be saved to that file.
        """
        self.log_uri = log_uri
        self.thread_name = thread_name
        self._print_formatter = logging.Formatter(None, None)
        self._file_formatter = logging.Formatter(self.LOG_FMT, self.DATE_FMT)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.NOTSET)

        if log_uri is not None:
            self.logfile_handler = logging.FileHandler(self.log_uri, mode='w')
        else:
            self.logfile_handler = logging.NullHandler()

        self.thread_filter = ThreadFilter(thread_name)
        self.error_queue_filter = ErrorQueueFilter()
        self.palisades_filter = PalisadesFilter()
        self.timed_filter = TimedProgressLoggingFilter(interval=5)

        self.logfile_handler.addFilter(self.thread_filter)
        self.logfile_handler.addFilter(self.palisades_filter)
        self.logfile_handler.addFilter(self.error_queue_filter)
        self.logfile_handler.addFilter(self.timed_filter)
        self.logfile_handler.setFormatter(self._file_formatter)

        self.logger.addHandler(self.logfile_handler)

    def print_args(self, args):
        """Log the input arguments dictionary to this manager's logfile.

            args - a python dictionary.

        Returns nothing."""

        # we want arguments to be printed very simply.

        sorted_args = sorted(args.iteritems(), key=lambda x: x[0])
        if len(sorted_args) > 0:
            max_key_width = max(map(lambda x:len(x[0]), sorted_args))
        else:
            max_key_width = 0

        format_str = "%-" + str(max_key_width) + "s %s"

        args_string = '\n'.join([format_str % (arg) for arg in sorted_args])
        args_string = "Printing arguments\nArguments:\n%s\n" % args_string
        self.logger.info(args_string)

    def print_errors(self):
        """Print all logging errors"""
        error_records = self.error_queue_filter.get_errors()
        if len(error_records) > 0:
            self.logfile_handler.removeFilter(self.error_queue_filter)
            self.logger.info('\n\n')
            self.logger.warn('Non-critical warnings found during execution:')
            for error_record in self.error_queue_filter.get_errors():
                self.logger.handle(error_record)
            self.logger.info('\n\n')
            self.logfile_handler.addFilter(self.error_queue_filter)

    def add_log_handler(self, handler, filter_palisades=False):
        """Add a logging handler.  Before the handler is added to the logger
        object, we also add a logging filter so that it only logs messages from
        this thread."""
        handler.addFilter(self.thread_filter)
        if filter_palisades:
            handler.addFilter(self.palisades_filter)
        handler.addFilter(self.timed_filter)
        self.logger.addHandler(handler)

    def remove_log_handler(self, handler):
        """Remove a logging handler."""
        handler.removeFilter(self.thread_filter)
        handler.removeFilter(self.error_queue_filter)
        handler.removeFilter(self.palisades_filter)
        handler.removeFilter(self.timed_filter)
        self.logger.removeHandler(handler)

    def print_message(self, message):
        """Print the input message to the log using the simple print formatter."""
        self.logfile_handler.setFormatter(self._print_formatter)
        self.logger.debug(message)
        self.logfile_handler.setFormatter(self._file_formatter)

    def close(self):
        """Close the logfile handler and un-register it from the LOGGER
        object."""
        self.logfile_handler.close()
        self.remove_log_handler(self.logfile_handler)


class Executor(threading.Thread):
    """Executor represents a thread of control that runs a python function with
    a single input.  Once created with the proper inputs, threading.Thread has
    the following attributes:

        self.module - the loaded module object provided to __init__()
        self.args   - the argument to the target function.  Usually a dict.
        self.func_name - the function name that will be called.
        self.log_manager - the LogManager instance managing logs for this script
        self.failed - defaults to False.  Indicates whether the thread raised an
            exception while running.
        self.execption - defaults to None.  If not None, points to the exception
            raised while running the thread.

    The Executor.run() function is an overridden function from threading.Thread
    and is started in the same manner by calling Executor.start().  The run()
    function is extremely simple by design: Print the arguments to the logfile
    and run the specified function.  If an execption is raised, it is printed
    and saved locally for retrieval later on.

    In keeping with convention, a single Executor thread instance is only
    designed to be run once.  To run the same function again, it is best to
    create a new Executor instance and run that."""
    def __init__(self, module, args, func_name='execute', log_file=None, tempdir=None):
        """Initialization function for the Executor.

            module - a python module that has already been imported.
            args - a python dictionary of arguments to be passed to the function
            func_name='execute'- a string.  Represents the name of the function
                to be called (e.g. module.func_name).  Defaults to 'execute'.
        """
        threading.Thread.__init__(self)
        self.module = module
        self.args = args
        self.func_name = func_name
        self.log_manager = LogManager(self.name, log_file)
        self.failed = False
        self.exception = None
        self.traceback = None
        self.tempdir = tempdir

    def run(self):
        """Run the python script provided by the user with the arguments
        specified.  This function also prints the arguments to the logfile
        handler.  If an exception is raised in either the loading or execution
        of the module or function, a traceback is printed and the exception is
        saved."""
        start_time = time.time()
        self.log_manager.print_args(self.args)
        try:
            function = getattr(self.module, self.func_name)
        except AttributeError as error:
            self.log_manager.logger.exception(error)
            self.failed = True
            raise AttributeError(('Unable to find function "%s" in module "%s" '
                'at %s') % (self.func_name, self.module.__name__,
                self.module.__file__))
        try:
            LOGGER.debug('Found function %s', function)
            LOGGER.debug('Starting model with args: \n%s',
                         pprint.pformat(self.args))
            with patch_tempdir(self.tempdir):
                function(self.args.copy())
        except Exception as error:
            # We deliberately want to catch all possible exceptions.
            LOGGER.exception(error)
            self.failed = True
            self.exception = error
            self.traceback = traceback.format_exc()
        finally:
            self.log_manager.print_errors()
            elapsed_time = round(time.time() - start_time, 2)
            self.log_manager.logger.info('Elapsed time: %s', format_time(elapsed_time))
            self.log_manager.logger.info('Execution finished')
            self.log_manager.close()


def format_time(seconds):
    """Render the integer number of seconds as a string.  Returns a string.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    hours = int(hours)
    minutes = int(minutes)

    if hours > 0:
        return "%sh %sm %ss" % (hours, minutes, seconds)

    if minutes > 0:
        return "%sm %ss" % (minutes, seconds)
    return "%ss" % seconds
