import threading

class Executor(threading.Thread):
    def __init__(self, module, args, func_name='execute'):
        threading.Thread.__init__(self)
        self.module = module
        self.args = args
        self.func_name = func_name

    def run(self):
        function = getattr(self.module, self.func_name)
        function(self.args)
