"""This file contains the core logic of the palisade package."""

import threading
import os
import json
import logging
import hashlib
import platform
from types import DictType
from types import StringType
from types import UnicodeType
import tempfile

import palisades.i18n.translation

class SignalNotFound(Exception):
    """A custom exception for when a signal was not found."""
    pass

_EXPAND_DIR = lambda x: os.path.expanduser(os.path.join(*x))
_SETTINGS_FOLDERS = {
    'Windows': _EXPAND_DIR(['~', 'Appdata', 'local', 'NatCap']),
    'Linux': _EXPAND_DIR(['~', '.natcap']),
    'Darwin': _EXPAND_DIR(['~', 'Library', 'Preferences', 'NatCap']),
    '': tempfile.gettempdir(),  # if python doesn't know the platform.
}
SETTINGS_DIR = _SETTINGS_FOLDERS[platform.system()]


LOGGER = logging.getLogger('utils')

class RepeatingTimer(threading.Thread):
    """A timer thread that calls a function after n seconds until the cancel()
    function is called."""
    def __init__(self, interval, function):
        threading.Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.finished = threading.Event()

    def cancel(self):
        """Cancel this timer thread at the next available opportunity.  Returns
        nothing."""
        self.finished.set()

    def run(self):
        while True:
            self.finished.wait(self.interval)
            if not self.finished.is_set():
                self.function()
            else:
                # If the thread has been cancelled, break out of the loop
                break

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

def apply_defaults(configuration, defaults, skip_duplicates=True,
        cleanup=False, old_defaults=None):
    """Take the input configuration and apply default values if and only if the
    configuration option was not specified by the user.

    configuration - a python dictionary of configuration options
    defaults - a python dictionary of default values.
    skip_duplicates - a Boolean.  If true, keys found in the configuration
        dictionary and in defaults wil be skipped.  If False, the defaults
        dictionary will be blindly applied to the configuration.  Defaults to
        True.
    cleanup - a boolean.  indicates whether to remove entries from
        configuration that are not in defaults.
    old_defaults - a dictionary or None.  If a dictionary, it should be of the
        current default dictionary.  If None, this indicates that no defaults
        should be considered.

    Returns a dictionary with rendered default values."""


    # Sanitize old_defaults for use later.
    if old_defaults is None:
        old_defaults = {}

    sanitized_config = configuration.copy()
    for key, default_value in defaults.iteritems():
        # If we find the current entry in the old_defaults dictionary AND the
        # value is the same as the old default value, we know that the default
        # value should be overridden with the new default value.
        if key in old_defaults:
            if old_defaults[key] == sanitized_config[key]:
                sanitized_config[key] = default_value

        try:
            if type(default_value) is DictType:
                default_value = apply_defaults(sanitized_config[key],
                    default_value, cleanup=cleanup)
                sanitized_config[key] = default_value
        except:
            # if the key is missing from the user's dictionary, we'll pass for
            # now.  It's handled below.
            pass

        if skip_duplicates:
            if key not in sanitized_config:
                sanitized_config[key] = default_value
        else:
            sanitized_config[key] = default_value


    if cleanup:
        for sanitized_key in sanitized_config.keys():
            if sanitized_key not in defaults:
                del sanitized_config[sanitized_key]

    return sanitized_config

def save_dict_to_json(dictionary, uri, indent=None):
    """Save a python dictionary to JSON at the specified URI."""
    if os.path.exists(uri):
        LOGGER.warn('File %s exists and will be overwritten.', uri)

    try:
        json_file = open(uri, mode='w+')
    except IOError:
        # IOError thrown when the folder structure of self.uri doesn't exist.
        os.makedirs(os.path.dirname(uri))
        json_file = open(uri, mode='w+')

    json_file.writelines(json.dumps(dictionary, indent=indent, sort_keys=True))
    json_file.close

def load_json(uri):
    """Load a JSON object from the file at URI.  Returns a python dictionary
    parsed from the JSON object at URI."""
    json_file = open(uri).read()
    return json.loads(json_file)

def get_md5sum(data_dict):
    """Get the MD5 hash for a dictionary of data.

        data_dict - a python dictionary to get the MD5sum from.

        Returns a string hash for the dictionary."""

    json_string = json.dumps(data_dict, sort_keys=True)
    data_md5sum = hashlib.md5(json_string).hexdigest()
    return data_md5sum

def add_translations_to_iui(config, lang_codes=['en'], current_lang='en'):
    # add translations to an IUI application
    new_config = config.copy()
    for known_key in palisades.i18n.translation.TRANS_KEYS:
        try:
            current_value = new_config[known_key]

            translations = dict((lang, None) for lang in lang_codes)
            translations[current_lang] = current_value

            new_config[known_key] = translations
        except KeyError:
            # the translateable key was not found, so we skip it.
            pass
    return new_config

def convert_iui(iui_config, lang_codes=['en'], current_lang='en'):
    # convert an iui configuration dictionary into a palisades-compatible
    # configuration dictionary.
    # iui_config is a dictoinary.
    # lang_codes (TODO LATER) - a list of string language codes to insert.
    # current_lang - a language string defining what language the config is
    # currently written in.
    # this is to be run before the language selection phase of configuration
    # reading.
    # returns a python dictionary that has been converted to palisades format.

    assert current_lang in lang_codes

    # before we start rebuilding all elements, search through the iui_config
    # and extract all of the enabledBy/disabledBy data.  This needs to be
    # extracted here, because IUI and palisades have very different
    # implementations of inter-element communication.

    # TODO: make this SAFE for OGRDropdown elements.
    connections = {}  # dict mapping {trigger_id: [(operation, target_id)]}

    iui_ops = {  # dict mapping IUI ops to palisades equivalents
        'enabledBy': 'enables',
        'disabledBy': 'disables',
    }

    def _locate_interactivity(element):
        if 'elements' in element:
            for element_config in element['elements']:
                _locate_interactivity(element_config)
        else:
            for connectivity_op in ['enabledBy', 'disabledBy']:
                if connectivity_op in element:
                    palisades_op = iui_ops[connectivity_op]
                    trigger_id = element[connectivity_op]
                    target_id = element['id']

                    op_tuple = (palisades_op, target_id)
                    try:
                        connections[trigger_id].append(op_tuple)
                    except KeyError:
                        connections[trigger_id] = [op_tuple]

    _locate_interactivity(iui_config)

    def recurse_through_element(element):
        new_config = add_translations_to_iui(element.copy(), lang_codes,
            current_lang)

        try:
            element_type = new_config['type']
        except KeyError:
            element_type = None

        try:
            signals = []
            element_ops = connections[new_config['id']]
            for operation, target_id in element_ops:
                signals.append("%s:%s" % (operation, target_id))
            new_config['signals'] = signals
        except KeyError:
            # If no connections were found for this IUI element, just pass.
            # Connections/inter-element connectivity is optional.
            pass

        # If enabledBy/disabledBy keys are found in the dictionary, delete
        # them.
        for interactivity_key in ['enabledBy', 'disabledBy']:
            try:
                del new_config[interactivity_key]
            except KeyError:
                # when the key is not there to be deleted, just skip.
                pass

        # If we have a hideableFileEntry, replace it with a file element that
        # has the hideable flag enabled.
        if element_type == 'hideableFileEntry':
            new_config['type'] = 'file'
            new_config['hideable'] = True

        # If we have a dropdown menu, the 'returns' options have changed
        # slightly.  If the user has not defined return configuration options,
        # skip the tweaking since defaults are assumed internally.
        if element_type == 'dropdown':
            try:
                return_type = new_config['returns']
                new_config['returns'] = {'type': return_type}
            except KeyError:
                pass

        if 'elements' in new_config:
            translated_elements_list = []
            for contained_config in new_config['elements']:
                try:
                    element_type = contained_config['type']
                except KeyError:
                    # If there's no type defined, then we just translate like
                    # normal.
                    element_type = None

                if element_type == 'list':
                    for list_element in contained_config['elements']:
                        translated_config = recurse_through_element(list_element)
                        translated_elements_list.append(translated_config)
                else:
                    translated_config = recurse_through_element(contained_config)
                    translated_elements_list.append(translated_config)

            new_config['elements'] = translated_elements_list
        return new_config

    return recurse_through_element(iui_config)

def expand_signal(shortform_signal):
    """Expand a signal from short-form to long-form.

    shortform_signal - a shortform signal string.

    Returns a longform signal dictionary."""

    if type(shortform_signal) not in [StringType, UnicodeType]:
        raise TypeError('shortform signal must be a string, %s found',
            type(shortform_signal))

    short_signal, element_id = shortform_signal.split(':')

    # tuples are (signal_name, target_function)
    _short_signals = {
        "enables": ("satisfaction_changed", "set_enabled"),
        "disables": ("satisfaction_changed", "set_disabled"),
    }

    try:
        signal_name, target_func = _short_signals[short_signal]
    except KeyError:
        LOGGER.error('Short-form signal %s is not known.',
            short_signal)
        raise RuntimeError('Short-form signal %s is not known' % short_signal)

    signal_config = {
        "signal_name": signal_name,
        "target": "Element:%s.%s" % (element_id, target_func),
    }

    return signal_config

def get_valid_signals(signal_config_list, known_signals):
    """Loop through signal configuration objects (whether short-form or
        long-form) and return a list of valid signal configuration options.

    signal_config_list - a list of long-or-short-form signal configuration
        objects. If a shortform configuration object is in this list, it will
        be expanded to a long-form object.  If a signal configuration object
        points to a signal that is not known, it will be skipped.
    known_signals - a list of signal strings that are known to the element in
        question.

    Returns a list of long-form signals that are valid for this element."""

    valid_signals = []
    for signal_config in signal_config_list:
        if type(signal_config) in [StringType, UnicodeType]:
            valid_signals.append(expand_signal(signal_config))

        elif type(signal_config) is DictType:
            if signal_config['signal_name'] not in known_signals:
                LOGGER.debug('Signal %s not in %s',
                    signal_config['signal_name'], known_signals)
                continue
            else:
                valid_signals.append(signal_config)

    return valid_signals

def setup_signal(signal_config, element_index):
    """Take a signal configuration object and set up the appropriate
    connections."""

    # If the signal configuration's target is a formatted target string (see
    # above for permitted formats), we need to know the target type.
    # Otherwise, we assume that the target is a python callable.
    if type(signal_config['target']) in [StringType, UnicodeType]:
        target_type = signal_config['target'].split(':')[0]
        target = signal_config['target'].replace(target_type + ':', '')

    else:  # assume that type(target) is FunctionType
        target_type = '_function'
        target = signal_config['target']  # just use the func given

    if target_type == 'Element':
        # assume element notation for now.  TODO: support more notations?
        element_id, element_funcname = target.split('.')
        try:
            target_element = element_index[element_id]
            target_func = getattr(target_element, element_funcname)
        except KeyError:
            # When there's no element known by that ID
            LOGGER.error(('Signal %s.%s could not find element with ID %s, '
                'skipping'), target_element.get_id('user'),
                signal_config['signal_name'], element_id)
            raise RuntimeError('Could not find element with id %s',
                element_id)
        except AttributeError as error:
            # When there's no function with the desired name in the target
            # element.
            LOGGER.error('Element "%s" has no function "%s".  Skipping.',
                element_id, element_funcname)
            raise error

    elif target_type == 'Python':
        # If the target type is Python, see if the target function is
        # in global first.
        if target in globals():
            target_func = globals()[target]
        else:
            # assume it's a python package path package.module.func
            path_list = target.split('.')
            target_module = execution.locate_module('.'.join(path_list[:-1]))
            target_func = getattr(target_module, path_list[-1])

    elif target_type == '_function':
        target_func = target  # just use the user-defined target


    return (signal_config['signal_name'], target_func)
