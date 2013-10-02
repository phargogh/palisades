import threading

class Executor(threading.Thread):
    def __init__(self, module, args):
        threading.Thread.__init__(self)
        self.module = module
        self.args = args

    def run(self):
        self.module.execute(self.args)
