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
import locale
import Queue
import sys

import palisades.i18n.translation


class SignalNotFound(Exception):
    """A custom exception for when a signal was not found."""
    pass


def _EXPAND_DIR(path_list):
    return os.path.expanduser(os.path.join(*path_list))


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
        # Interesting discussion on threading.event.wait() vs. time.sleep
        # here: http://stackoverflow.com/a/29082411/299084
        while not self.finished.wait(self.interval):
            self.function()


class CommunicationWorker(threading.Thread):
    def __init__(self, target, args=(), kwargs={}, response_queue=None):
        threading.Thread.__init__(self)
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.response_queue = response_queue

    def run(self):
        try:
            self.target(*self.args, **self.kwargs)
        except Exception as error:
            LOGGER.exception('Failure in thread %s', self.name)
            if self.response_queue:
                self.response_queue.put(sys.exc_info())


class Communicator(object):
    """Element represents the base class for all UI elements.  It focuses
    on inter-element connectivity and communication."""
    # signals is a list of dictionaries
    # signal['target'] - a pointer to the signal's target element and function
    # signal['condition'] - the condition under which this signal is emitted
    # When a signal is emitted, data about the signal should also be passed.
    def __init__(self):
        self.callbacks = []
        self.callback_queue = Queue.Queue()
        self.response_queue = Queue.Queue()
        self.lock = threading.RLock()
        self._exceptions = []

    def register(self, callback, *args, **kwargs):
        """Register a callback function and optional arguments.

        Any additional arguments provided by ``*args`` or ``**kwargs`` will be
        registered to the function as well and, when ``emit()`` is called,
        the target callback will be called with these arguments.

        Parameters:
            callback (callable): a callable that takes at least one
                user-defined argument.

        Returns:
            ``None``
        """
        data = {
            'func': callback,
            'args': args,
            'kwargs': kwargs,
        }
        with self.lock:
            self.callbacks.append(data)

    def emit(self, argument, join=False):
        """Call all of the registered callback functions with the argument
        passed in.

        argument - the object to be passed to all callbacks.

        Returns nothing."""
        with self.lock:
            # clear out the response queue
            self._exceptions = []
            while not self.response_queue.empty():
                self.response_queue.get()

            # load up the queue
            for callback_data in self.callbacks:
                self.callback_queue.put(callback_data)
            self.callback_queue.put('STOP')

            try:
                threads = []
                while True:
                    callback_data = self.callback_queue.get()
                    if callback_data == 'STOP':
                        break

                    t = CommunicationWorker(
                        target=callback_data['func'],
                        args=(argument,) + callback_data['args'],
                        kwargs=callback_data['kwargs'],
                        response_queue=self.response_queue)

                    t.start()
                    threads.append(t)
            finally:
                if join:
                    for thread in threads:
                        thread.join()

    def exceptions(self):
        if not self.response_queue.empty():
            exceptions = []
            with self.lock:
                while not self.response_queue.empty():
                    exceptions.append(self.response_queue.get())
        else:
            exceptions = self._exceptions

        return exceptions


    def remove(self, target):
        """Remove a matching callback from the list of callbacks.

        Parameters:
            target (callable): a callable that has been registered as a
                callback in this Communicator instance.

        Returns:
            ``None``

        Raises:
            SignalNotFound: When the callback was not found.
        """
        with self.lock:
            try:
                callbacks_list = [cb['func'] for cb in self.callbacks]
                self.lock.acquire()
                index = callbacks_list.index(target)
                self.callbacks.pop(index)
            except ValueError:
                # want to raise a custom exception here so that it's independent of
                # implementation details in this class.
                raise SignalNotFound(
                    ('Callback %s ' % str(target),
                     'was not found or was previously removed'))


def decode_string(bytestring):
    """
    Decode the input bytestring to one of a couple of possible known encodings.

    """

    for codec in [locale.getpreferredencoding(), 'utf-8', 'latin-1', 'ascii']:
        try:
            return bytestring.decode(codec)
        except UnicodeEncodeError:
            return bytestring.encode(codec)
        except UnicodeDecodeError:
            pass
    LOGGER.warn("Wasn't able to decode string %s" % bytestring)
    return bytestring


def apply_defaults(configuration, defaults):
    """Applies defaults to the configuration dict.

    Take the input configuration and apply default values if and only if the
    configuration option was not specified by the user.

    Parameters:
        configuration - a python dictionary of configuration options
        defaults - a python dictionary of default values.

    Returns:
        A dict with rendered default values."""

    primitive_types = [int, float, basestring, str, unicode]
    iterable_types = [list, dict]

    # a = user config
    # b = defaults
    def merge(a, b, path=None):
        "merges b into a"
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    a[key] = merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass  # same leaf value
                elif ((type(a[key]) in primitive_types and
                        type(b[key]) in primitive_types) or
                        (type(a[key] in iterable_types) and
                         type(b[key] in iterable_types))):
                    # When types are both primitive or both iterable but
                    # values differ, use the user's value.
                    pass
                else:
                    raise TypeError('Conflict at %s' %
                                    '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a

    return merge(configuration, defaults)


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

    connections = {}  # dict mapping {trigger_id: [(operation, target_id)]}
    def add_connection(palisades_op, trigger, target_id):
        op_tuple = (palisades_op, target_id)
        try:
            connections[trigger].append(op_tuple)
        except KeyError:
            connections[trigger] = [op_tuple]

    iui_ops = {  # dict mapping IUI ops to palisades equivalents
        'enabledBy': 'enables',
        'disabledBy': 'disables',
        'requiredIf': 'set_required',
    }

    def _locate_interactivity(element):
        if 'elements' in element:
            for element_config in element['elements']:
                _locate_interactivity(element_config)
        else:
            for connectivity_op in iui_ops.keys():
                if connectivity_op in element:
                    # palisades_op represneents the palisades shortform signal
                    # type (enables, disables, set_required, etc.)
                    palisades_op = iui_ops[connectivity_op]

                    trigger_id = element[connectivity_op]
                    target_id = element['id']

                    # requiredIf triggers are a list.  Conform to this.
                    if connectivity_op in ['requiredIf']:
                        trigger_id_list = trigger_id
                    else:
                        trigger_id_list = [trigger_id]

                    # OGR/CSV dropdowns in IUI use the 'enabledBy' key to serve
                    # several purposes: enable the dropdown AND fetch the
                    # value of the table file from the enabling element.
                    # This allows the element that enables the table dropdown
                    # to have two signals, both pointint to the table dropdown.
                    if ((connectivity_op == 'enabledBy') and
                            (element['type'] in ['CSVFieldDropdown',
                                                 'OGRFieldDropdown'])):
                        add_connection(palisades_op, trigger_id, target_id)
                        palisades_op = 'populate_tabledropdown'

                    # This is iterable because requiredIf might well have many
                    # elements that it links to.
                    for trigger in trigger_id_list:
                        add_connection(palisades_op, trigger, target_id)

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

        # If interactivity keys are found in the dictionary, delete
        # them.  They have been replaced by signal configurations.
        for interactivity_key in iui_ops.keys():
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

        # rename the tabbedGroup element, as needed.
        if element_type == 'tabbedGroup':
            new_config['type'] = 'tabGroup'

        if element_type == 'hiddenElement':
            new_config['type'] = 'hidden'

        # The 'dataType' value is now stored in the 'returns' dict.
        if 'dataType' in new_config:
            try:
                new_config['returns']['type'] = new_config['dataType']
            except (KeyError, TypeError):
                new_config['returns'] = {'type': new_config['dataType']}
            del new_config['dataType']

        # If we have a dropdown menu, the 'returns' options have changed
        # slightly.  If the user has not defined return configuration options,
        # skip the tweaking since defaults are assumed internally.
        # Also, 'options' are now translateable.
        if (element_type in ['checkbox'] or
                'dropdown' in unicode(element_type).lower()):
            try:
                return_type = new_config['returns']
                if isinstance(return_type, dict):  # when this is a mapValues dict
                    new_config['returns'] = {
                        'type': 'string',
                        'mapValues': return_type['mapValues'],
                    }
                else:  # either string or ordinal
                    # Strip off the trailing `s` from the return type
                    new_config['returns'] = {'type': return_type[:-1]}
            except KeyError:
                pass

        # If we have a multielement, rename the sampleElement -> template
        if element_type == 'multi':
            new_config['template'] = new_config['sampleElement']
            del new_config['sampleElement']

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
        "set_required": ("satisfaction_changed", "set_conditionally_required"),
        "populate_tabledropdown": ("value_changed", "load_columns"),
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

    # having asserted that all signals in requested_signals are known, we
    # can try to connect the communicators to their targets.
    # TARGET FORMS:
    #    element notation: Element:<element_id>.func_name
    #    python notation: Python:package.module.function
    #
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
            LOGGER.error(('Signal %s could not find element with ID %s, '
                'skipping'), signal_config['signal_name'], element_id)
            raise KeyError('Could not find element with id %s',
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


def settings_folder():
    """Return the file location of the user's settings folder.  This folder
    location is OS-dependent."""
    if platform.system() == 'Windows':
        config_folder = os.path.join('~', 'AppData', 'Local', 'NatCap')
    else:
        config_folder = os.path.join('~', '.natcap')

    expanded_path = os.path.expanduser(config_folder)
    return expanded_path


def get_user_language():
    """Fetch the user's preferred language, if the user has defined one.

    If the user has not configured a language or the configuration cannot be
    parsed, RuntimeError is raised.
    """
    config_file_location = os.path.join(settings_folder(),
                                        'user_config.json')
    try:
        return json.load(
            open(config_file_location))['preferred_lang']
    except (IOError, ValueError):
        # IOError when the file doesn't exist yet.
        # ValueError when a JSON object can't be decoded
        raise RuntimeError('User language could not be read from config.')

def save_user_language(user_lang_choice):
    """Save the user's language selection to the config file."""
    config_file_location = os.path.join(settings_folder(),
                                        'user_config.json')

    json.dump({'preferred_lang': user_lang_choice},
                open(config_file_location, 'w'))
