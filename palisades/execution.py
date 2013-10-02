import threading
import logging

logging.basicConfig(format='%(asctime)s %(name)-18s %(threadName)-10s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('')

class ThreadFilter(logging.Filter):
    def __init__(self, thread_name):
        logging.Filter.__init__(self)
        self.thread_name = thread_name

    def filter(self, record):
        if record.threadName == self.thread_name:
            return True
        return False

class Executor(threading.Thread):
    def __init__(self, module, args, func_name='execute'):
        threading.Thread.__init__(self)
        self.module = module
        self.args = args
        self.func_name = func_name

        # Set up the log file writing here as a logging FileHandler.
        log_fmt = "%(asctime)s %(name)-18s %(levelname)-8s %(message)s"
        date_fmt = "%m/%d/%Y %H:%M:%S "
        formatter = logging.Formatter(log_fmt, date_fmt)
        self.fh = logging.FileHandler('log-%s.foo' % self.name)
        self.fh.setFormatter(formatter)
        self.fh.addFilter(ThreadFilter(self.name))
        LOGGER.addHandler(self.fh)

    def __del__(self):
        LOGGER.removeHandler(self.fh)

    def run(self):
        function = getattr(self.module, self.func_name)
        function(self.args)


