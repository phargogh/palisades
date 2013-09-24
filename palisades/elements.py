from palisades import fileio

ELEMENTS = {}
LAYOUT_VERTICAL = 0


class Application(object):
    def __init__(self, config_uri):
        configuration = fileio.read_config(config_uri)
        print configuration
