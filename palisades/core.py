"""This file contains the core logic of the palisade package."""

LAYOUT_VERTICAL_LIST = 1
LAYOUT_HORIZONTAL_LIST = 2
LAYOUT_GRID = 3


class SignalNotFound(Exception):
    """A custom exception for when a signal was not found."""
    pass

class Communicator(object):
    """Element represents the base class for all UI elements.  It focuses
    on inter-element connectivity and communication."""
    # signals is a list of dictionaries
    # signal['target'] - a pointer to the signal's target element and function
    # signal['condition'] - the condition under which this signal is emitted
    # When a signal is emitted, data about the signal should also be passed.
    def __init__(self):
        self.callbacks = []

    def register(self, callback):
        """This function appends the target function call to the list of
        signals stored by this element"""

        self.callbacks.append(callback)

    def emit(self, argument):
        """Call all of the registered callback functions with the argument
        passed in.

        argument - the object to be passed to all callbacks.

        Returns nothing."""

        for callback_func in self.callbacks:
            callback_func(argument)

    def remove(self, target):
        """"""
        try:
            callbacks_list = [cb for cb in self.callbacks]
            index = callbacks_list.index(target)
            self.callbacks.pop(index)
        except ValueError:
            # want to raise a custom exception here so that it's independent of
            # implementation details in this class.
            raise SignalNotFound(('Signal %s ' % str(target),
                'was not found or was previously removed'))

def apply_defaults(configuration, defaults, skip_duplicates=True):
    """Take the input configuration and apply default values if and only if the
    configuration option was not specified by the user.

    configuration - a python dictionary of configuration options
    defaults - a python dictionary of default values.
    skip_duplicates - a Boolean.  If true, keys found in the configuration
        dictionary and in defaults wil be skipped.  If False, the defaults
        dictionary will be blindly applied to the configuration.  Defaults to
        True.

    Returns a dictionary with rendered default values."""

    sanitized_config = configuration.copy()
    if skip_duplicates:
        for key, default_value in defaults.iteritems():
            if key not in sanitized_config:
                sanitized_config[key] = default_value
    else:
        sanitized_config.update(defaults)

    return sanitized_config
