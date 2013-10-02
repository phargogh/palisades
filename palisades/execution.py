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

class Executor(threading.Thread):
    def __init__(self, module, args, func_name='execute', log_file=None):
        """Initialization function for the Executor.

            module - a python module that has already been imported.
            args - a python dictionary of arguments to be passed to the function
            func_name='execute'- a string.  Represents the name of the function
                to be called (e.g. module.func_name).  Defaults to 'execute'.
            log_file=None - a URI or None.  If a URI is given, all logging will
                be saved to that file.  If None, logging will not be saved to a
                file.
        """
        threading.Thread.__init__(self)
        self.module = module
        self.args = args
        self.func_name = func_name
        self.log_file = log_file

        # If the user provided a log file URI, then we save the log file there.
        # If no log file provided, skip saving to a log file.
        if log_file is not None:
            # Set up the log file writing here as a logging FileHandler.
            log_fmt = "%(asctime)s %(name)-18s %(levelname)-8s %(message)s"
            date_fmt = "%m/%d/%Y %H:%M:%S "
            formatter = logging.Formatter(log_fmt, date_fmt)
            self.fh = logging.FileHandler(log_file)
            self.fh.setFormatter(formatter)
            self.fh.addFilter(ThreadFilter(self.name))
            LOGGER.addHandler(self.fh)

    def __del__(self):
        """Descructor function for the Thread object.  We want to remove the
        file pointer from the logging object when the thread is finished so we
        know for sure that no other data will be written to it."""
        if self.log_file is not None:
            LOGGER.removeHandler(self.fh)

    def run(self):
        function = getattr(self.module, self.func_name)
        function(self.args)


