import threading
import logging

logging.basicConfig(format='%(asctime)s %(name)-18s %(threadName)-10s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('')

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

def print_args(function, args_dict):
    """Write args_dict to a formatted string to the user-defined function.
        args_dict - a dictionary.

    returns noting"""

    function("Arguments:")
    sorted_args = sorted(args_dict.iteritems(), key=lambda x: x[0])
    max_key_width = max(map(lambda x:len(x[0]), sorted_args))
    format_str = "%-" + str(max_key_width) + "s %s"
    for name, value in sorted_args:
        function(format_str % (name, value))
    function("")

def locate_module(self, module):
    """Locate and import the requested module.

        module - a python string, either in python's package.subpackage.module
            notation or a URI on disk.

        Returns a tuple of (executeable module, module name)"""

    if os.path.isfile(module):
        model = imp.load_source('model', module)
       # Model name is name of module file, minus the extension
        model_name = os.path.splitext(os.path.basename(module))[0]
        LOGGER.debug('Loading %s from %s', model_name, model)
    else:
        LOGGER.debug('PATH: %s', sys.path)
        module_list = module.split('.')
        model = _get_module_from_path(module_list)
        model_name = module_list[-1]  # model name is last entry in list
        LOGGER.debug('Loading %s from PATH', model_name)
    return (model, model_name)

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

    current_name = module_list[0]
    module_info = imp.find_module(current_name, path)
    imported_module = imp.load_module(current_name, *module_info)

    if len(module_list) > 1:
        return _get_module_From_path(module_list[1:], imported_module.__path__)
    else:
        return imported_module

class PythonRunner():
    def __init__(self, module_string, args, func_name='execute', post_run=[]):
        module, module_name = locate_module(module_string)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d--%H_%M_%S")
        filename = '%s-log-%s.txt' % (module_name, timestamp)

        log_file_uri = os.path.join(args['workspace_dir'], filename)
        self.executor = Executor(module, args, func_name, log_file_uri)

        # TODO: Add some communicators here, in case other objects are
        # interested in executor-related events.

    def start(self):
        self.executor.start()



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
        self._print_formatter = logging.Formatter(None, None)
        self._file_formatter = logging.Formatter(self.LOG_FMT, self.DATE_FMT)

        if log_uri is not None:
            self.logfile_handler = logging.FileHandler(self.log_uri, mode='w')
        else:
            self.logfile_handler = logging.NullHandler()

        self.logfile_handler.addFilter(ThreadFilter(thread_name))
        self.logfile_handler.setFormatter(self._file_formatter)
        LOGGER.addHandler(self.logfile_handler)

    def print_args(self, args):
        """Log the input arguments dictionary to this manager's logfile.

            args - a python dictionary.

        Returns nothing."""

        # we want arguments to be printed very simply.
        self.logfile_handler.setFormatter(self._print_formatter)

        LOGGER.debug("Arguments:")
        sorted_args = sorted(args.iteritems(), key=lambda x: x[0])
        if len(sorted_args) > 0:
            max_key_width = max(map(lambda x:len(x[0]), sorted_args))
        else:
            max_key_width = 0

        format_str = "%-" + str(max_key_width) + "s %s"
        for name, value in sorted_args:
            LOGGER.debug(format_str % (name, value))
        LOGGER.debug("")

        # Restore the logfile formatter to the full file formatting.
        self.logfile_handler.setFormatter(self._file_formatter)

    def close(self):
        """Close the logfile handler."""
        self.logfile_handler.close()


class Executor(threading.Thread):
    def __init__(self, module, args, func_name='execute', log_file=None):
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


    def run(self):
        self.log_manager.print_args(self.args)
        try:
            function = getattr(self.module, self.func_name)
            function(self.args)
        except:
            LOGGER.debug('error encountered')
            # log some debug information here
        finally:
            self.log_manager.close()


