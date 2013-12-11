"""This file contains the core logic of the palisade package."""

import threading
import os
import json
import logging
import hashlib
from types import DictType

import palisades.i18n.translation

class SignalNotFound(Exception):
    """A custom exception for when a signal was not found."""
    pass

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
    for key, default_value in defaults.iteritems():
        try:
            if type(default_value) is DictType:
                default_value = apply_defaults(sanitized_config[key], default_value)
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

    json_file.writelines(json.dumps(dictionary, indent=indent))
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

    def recurse_through_element(element):
        new_config = add_translations_to_iui(element.copy(), lang_codes,
            current_lang)

        try:
            element_type = new_config['type']
        except KeyError:
            element_type = None

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

