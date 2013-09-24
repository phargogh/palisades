import json

def read_config(config_uri):
    """Read in the configuration file and parse out the structure of the target
    user interface.

        config_uri - a URI to a JSON file on disk.

    Returns a python dictionary."""

    config_file = open(config_uri).read()
    return json.loads(config_file)


