import os
import logging
from types import *
import re

from palisades import fileio
from palisades import utils
from palisades.utils import Communicator
from palisades import validation
from palisades import execution
from palisades.i18n import translation
import palisades.gui
import palisades.i18n

LOGGER = logging.getLogger('palisades.elements')

class InvalidData(ValueError):
    def __init__(self, problem_data):
        ValueError.__init__(self)
        self.data = problem_data

    def __str__(self):
        return 'Inputs have errors: %s' % repr(self.data)

class ValidationStarted(RuntimeError): pass
class ElementDisabled(RuntimeError): pass
class InteractionError(RuntimeError): pass

def get_elements_list(group_pointer):
    """Construct a data structure with pointers to the elements of the group.

        group_pointer - a reference to a Group instance.

    Returns a list of elements and lists.  Example:
        [element, element, element, [element, element]]
    """
    #TODO: test this function.
    def _recurse_through_elements(elem_list):
        new_elements = []

        for elem in elem_list:
            if isinstance(elem, Primitive):
                new_elements.append(elem)
            else:
                new_elements.append(_recurse_through_elements,
                    elem.elements)
        return new_elements

    return _recurse_through_elements(group_pointer.elements)

# Assume this is a window for a moment.
class Application(object):
    def __init__(self, config_uri, lang_code='en'):
        # if GUI is None, have to visual display.
        # install the specified internal language.
        palisades.i18n.language.set(lang_code)
        allowed_langs, configuration = translation.translate_json(config_uri, lang_code)
        self.config_langs = allowed_langs
        self._window = Form(configuration)
        self._window.set_langs(allowed_langs)
        self._window.emit_signals()

class Element(object):
    """Element contains the core logic and interactivity required by all
    palisades element.

    Public Attributes:
        self.config - the rendered configuration options used by the Element
            class.  This is a dictionary containing at least default options.
        self.config_changed - a communicator.  Triggered when the
            configuration is changed.
        self.value_changed - a communicator.  Triggered when the value is
            changed.
        self.interactivity_changed - a communicator.  Triggered when the
            element's is either disabled or enabled.


    Private Attributes:
        self._enabled - boolean, indicates whether the element is enabled.
        self._parent_ui - a reference to the parent UI.
        self._default_config - a dictionary containing default configuration
            options.
    """
    defaults = {
        "enabled": True,
    }

    def __init__(self, configuration, parent=None):
        object.__init__(self)
        self._visible = True

        self._parent_ui = parent
        self._default_config = {}
        self._hashable_config = []  # keys corresponding to config keys to hash

        # Set up the communicators
        self.config_changed = Communicator()
        self.interactivity_changed = Communicator()
        self.visibility_changed = Communicator()
        self.satisfaction_changed = Communicator()

        # Render the configuration and save to self.config
        self.config = utils.apply_defaults(configuration, self.defaults)

        # set element attributes
        LOGGER.debug('config = %s', self.config)
        self._enabled = self.config['enabled']

    @property
    def signals(self):
        """Return a list of string names of all attributes of this class that
        are Communicator instances."""

        signals = []
        for attr_name, attr_obj in self.__dict__.iteritems():
            if isinstance(attr_obj, Communicator):
                signals.append(attr_name)

        return signals

    def emit_signals(self):
        """Emit all signals with their appropriate value.  Returns nothing."""
        self.config_changed.emit(self.config)
        self.interactivity_changed.emit(self.is_enabled())
        self.visibility_changed.emit(self.is_visible())
        self.satisfaction_changed.emit(self.is_satisfied())

    def set_default_config(self, new_defaults):
        """Add default configuration options to this Element instance's default
        config dictionary.  If this function is called after the element's UI
        representation is created, it will trigger the UI representation to
        reload the configuration.

        new_defaults - a python dictionary of default values.  Any duplicate keys
            contained in this new dictionary will overwrite existing defaults.

        Triggers the config_changed signal to be emitted with the new
        configuration.

        Returns nothing."""

        old_defaults = self._default_config.copy()
        self._default_config.update(new_defaults)
        self.config = utils.apply_defaults(self.config, self._default_config,
                old_defaults=old_defaults)
        self.config_changed.emit(self.config)

    def is_enabled(self):
        """Query whether this element is enabled, indicating whether this
        element can be interacted with by the user.

        If this element is currently invisible, False will always be returned.

        Returns a boolean."""

        if self.is_visible():
            return self._enabled
        return False

    def set_disabled(self, new_state):
        """Enable or disable this element.

        new_state - A boolean.  If True, disable this element.  If False,
            enable this element.

        NOTE: this is an inverted wrapper around set_enabled()."""

        self.set_enabled(not new_state)

    def set_enabled(self, new_state):
        """Enable or disable this element.

        new_state - A boolean.  If True, enable this element.  If False, disable
            this element.

        If the enabled state of this element changes, the interactivity_changed
        signal is emitted with the new state.

        Returns nothing."""

        prev_satisfaction = self.is_satisfied()

        LOGGER.debug('Calling set_enabled with %s (current=%s)', new_state,
            self._enabled)
        new_state = bool(new_state)

        if new_state != self._enabled:
            self._enabled = new_state
            LOGGER.debug('element %s emitting interactivity_changed',
                self.get_id('user'))
            self.interactivity_changed.emit(new_state)

        if prev_satisfaction != self.is_satisfied():
            LOGGER.debug('Element %s has updated satisfaction to %s, emitting',
                self.get_id('user'), self.is_satisfied())
            self.satisfaction_changed.emit(self.is_satisfied())

    def is_visible(self):
        """Query whether this element is visible and return the visibility
        state.

        Returns a boolean."""

        return self._visible

    def set_visible(self, new_visibility):
        """Show or hide this element to the user.

        new_visibility - a Boolean.  If True, show this element.  If False, hide
            this element.

        If the visibility of this element changes, the visibility_changed signal
        is emitted with the new visibility status.

        Note that making an element visible does not necessarily mean that it's
        interactive.  An element could be visible and noninteractive.  When an
        element is invisible, it is not interactive.

        Returns Nothing."""

        assert type(new_visibility) is BooleanType, 'Visibility must be True or False'

        # If visibility is changing, set the new visibility state and emit the
        # visibility_changed signal.
        if new_visibility != self.is_visible():
            self._visible = new_visibility
            self.visibility_changed.emit(self._visible)

    def set_state(self, state):
        raise Exception('Must be implemented for subclasses')

    def state(self):
        raise Exception('Must be implemented for subclasses')

    def _get_hashable_config(self):
        """Get the hashable configuration dictionary."""
        hashable_obj = {}
        for config_key, value in self._default_config.iteritems():
            if config_key in self._hashable_config:
                hashable_obj[config_key] = value

        # we always want to add certain object information, so add that here.
        hashable_obj['classname'] = self.__class__.__name__
        try:
            hashable_obj['args_id'] = self.config['args_id']
        except KeyError:
            # if there's no args_id for this element, skip it.
            pass

        LOGGER.debug('Hashable object: %s', hashable_obj)
        return hashable_obj

    def get_id(self, id_type='md5sum'):
        # md5sum represents a hash of relevant element attributes.
        # user represents the user-defined identifier, if provided (None if not
        # provided in JSON config)
        # TODO: make this work for Groups.
        assert id_type in ['md5sum', 'user']

        if id_type == 'md5sum':
            return utils.get_md5sum(self._get_hashable_config())
        else: # id type must be user-defined
            try:
                return self.config['id']
            except KeyError:
                # If the user did not specify an ID, then there is no user key.
                # when this happens, get the md5sum ID instead.
                return self.get_id('md5sum')

    def is_satisfied(self):
        """Basic function to test whether this element is satisfied.
        Subclasses may override this to provide input-specific satisfaction
        requireents.

        An element, at its most simplistic, is satisfied when it is enabled,
        and not satisfied when it is not.  Returns a boolean."""
        return self.is_enabled()


class Primitive(Element):
    """Primitive represents the simplest input element."""
    defaults = {
        'validateAs': {'type': 'disabled'},
        'hideable': False,
        'required': False,
        'enabled': True,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        Element.__init__(self, configuration)
        self._value = None

        # self._valid has 3 possible states:
        #   None -  indicates validation has not been performed on this value or
        #           else validation is in progress.
        #   True -  value passes validation.
        #   False - value fails validation (either validation failure or a
        #           warning)
        self._valid = None
        self._validation_error = None
        self._hashable_config = ['hideable', 'validateAs']

        # Set up our Communicator(s)
        self.value_changed = Communicator()
        self.validation_completed = Communicator()
        self.hidden_toggled = Communicator()
        self.validity_changed = Communicator()

        # update the default configuration and set defaults based on the config.
        self.set_default_config(self.defaults)
        self._hidden = self.config['hideable']
        self._hideable = self.config['hideable']
        self._required = self.config['required']
        self._conditionally_required = False
        self._satisfied = False

        # Set up our validator
        self._validator = validation.Validator(
            self.config['validateAs']['type'])
        self._validator.finished.register(self._get_validation_result)

    def emit_signals(self):
        self.value_changed.emit(self.value())
        self.hidden_toggled.emit(self.is_hidden())
        self.validity_changed.emit(self._valid)

        #TODO: not sure if this should even be emitted.  Skipping for now.
        #self.validation_completed.emit(self._valid)
        Element.emit_signals(self)

    def reset_value(self):
        """Reset the element's value to its default value, as defined in the
        configuration.

        Returns nothing."""
        default_value = self.config['defaultValue']
        self.set_value(default_value)

    def set_value(self, new_value):
        """Set the value of this element.  If the element's value changes, all
        registered callbacks will be emitted.

        Returns nothing."""

        LOGGER.debug('%s setting value to %s', self.get_id('user'), new_value)
        if not self.is_enabled():
            return

        # If the value of this element has changed, we want to trigger all the
        # elements that requested notification.
        old_value = self.value()
#        if old_value != new_value:
        self._value = new_value
        self._valid = None
        self.value_changed.emit(new_value)
        self.validate()

    def value(self):
        """Get the value of this element."""
        return self._value

    def is_valid(self):
        """Return the validity of this input.  If an element has not been
        validated, it will be validated here and will block until validation
        completes.  Returns a Boolean.
        """
        # If we don't know the validity and the validator has finished
        if self._valid == None and self._validator.thread_finished() == True:
            self.validate()

        if self._validator.thread is None:
            self.validate()

        self._validator.join()

        # Return whether validation passed (a boolean).
        if self.has_input():
            return self._valid
        else:
            if self.is_required():
                return self._valid
            else:
                return True  # if no input and optional, input is valid.

    def validate(self):
        # if validation is already in progress, block until finished.
        while not self._validator.thread_finished():
            pass

        if self.config['required'] and not self.has_input():
            LOGGER.debug('Element %s is required' % self)
            elem_req_msg = _('Element is required')
            elem_req_state = validation.V_FAIL
            self._get_validation_result((elem_req_msg, elem_req_state))
            return

        validation_dict = self.config['validateAs'].copy()
        validation_dict['value'] = self.value()
        self._validator.validate(validation_dict)  # this starts the thread

    def _get_validation_result(self, error):
        """Utility class method to get the error result from the validator
        object.  Sets self._valid according to whether validation passed or
        failed, and sets the validation error to the error found (if any).

        error - a tuple of (error_msg, error_state)."""
        error_msg, state = error

        prev_satisfaction = self._satisfied
        LOGGER.debug('prev_satisfaction: %s', prev_satisfaction)
        old_validity = self._valid

        if state == validation.V_PASS:
            self._valid = True
        else:
            self._valid = False

        # if validity changed, emit the validity_changed signal
        if old_validity != self._valid:
            LOGGER.debug('Validity of "%s" changed from %s to %s',
                self.get_id('user'), old_validity, self._valid)
            self.validity_changed.emit(self._valid)

        LOGGER.debug('Emitting validation_completed')
        try:
            if len(error_msg) > 0:
                LOGGER.debug('Validation error: %s', error_msg)
        except TypeError:
            # when error_msg is None, there's no len().
            # Error_msg of None means no validation error.
            pass

        self._validation_error = error_msg
        self.validation_completed.emit(error)

        LOGGER.debug('current satisfaction: %s', self.is_satisfied())
        self._satisfied = self.is_satisfied()
        if self.is_satisfied() != prev_satisfaction:
            LOGGER.debug('Satisfaction changed for %s', self.get_id('user'))
            self.satisfaction_changed.emit(self.is_satisfied())

    def is_hideable(self):
        return self._hideable

    def set_hidden(self, is_hidden):
        assert type(is_hidden) is BooleanType, ('is_hidden must be Boolean'
            ', %s found instead' % is_hidden.__class__.__name__)

        if self._hidden != is_hidden:
            self._hidden = is_hidden
            self.hidden_toggled.emit(is_hidden)

    def is_hidden(self):
        return self._hidden

    def is_satisfied(self):
        """Determine if this element has satisfactory input.  An element is
        satisfied if both these requirements are met:
            - The element must have input
            - The element's validation must pass (if it has validation)
            - The element must be enabled.
        Returns a boolean with the satisfaction state."""

        if self.has_input() and self._valid and self.is_enabled():
            return True
        return False

    def state(self):
        """Return a python dictionary describing the state of this element."""
        state_dict = {
            'value': self.value(),
            'is_hidden': self.is_hidden()
        }
        return state_dict

    def set_state(self, state):
        """Set the state of this Element.

            state - a python dictionary defining the state of this element.
                Must have the following attributes:
                    'value' -> some pythonic value relevant to this element.
                    'is_hidden' -> a boolean.  Ignored if not hideable.
        """
        self.set_value(state['value'])
        self.set_hidden(state['is_hidden'])

    def is_required(self):
        if self._required:
            return self._required
        return self._conditionally_required

    def set_conditionally_required(self, cond_require):
        self._conditionally_required = cond_require

    def has_input(self):
        if self.value() != None:
            return True
        return False

    def should_return(self):
        LOGGER.debug('Checking whether should return: %s (%s)',
                     self, self.get_id('user'))
        # if element does not have an args_id, we're not supposed to return.
        # Therefore, return False.
        if 'args_id' not in self.config:
            LOGGER.debug('Element %s does not have an args_id', self)
            return False

        return_if_hidden = self.config['returns']['ifHidden']
        if return_if_hidden or self.is_hidden():
            LOGGER.debug('Element %s is hidden.', self)
            return False

        # if element is disabled and we're not supposed to return if disabled,
        # return False.
        return_if_disabled = self.config['returns']['ifDisabled']
        if self.is_enabled() is False:
            if return_if_disabled is False:
                LOGGER.debug('Element %s is disabled and should not return',
                    self)
                return False

        # if the element is empty and we're not supposed to return if it's
        # empty, return False.  This is only the case when element is not
        # required.
        return_if_empty = self.config['returns']['ifEmpty']
        required = self.config['required']
        if (not return_if_empty and not self.has_input()) and not required:
            LOGGER.debug('Element %s (%s) is empty', self,
                    self.config['args_id'])
            return False

        # If none of the previous conditions have been met, return True.
        return True

    def help_text(self):
        """Returns the helpText attribute string."""
        return self.config['helpText']

class LabeledPrimitive(Primitive):
    defaults = {
        'label': u'',
        'helpText': '',
        'validateAs': {'type': 'disabled'},
        'enabled': True,
        'hideable': False,
        'required': False,
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        Primitive.__init__(self, configuration)
        self._hashable_config = ['hideable', 'validateAs', 'label']

        self.set_default_config(self.defaults)
        self._label = self.config['label']

    def set_label(self, new_label):
        cast_label = new_label.decode("utf-8")
        self._label = cast_label

    def label(self):
        return self._label

class Dropdown(LabeledPrimitive):
    defaults = {
        'options': ['No options specified'],
        'defaultValue': 0,
        'validateAs': {'type': 'disabled'},
        'enabled': True,
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
            'type': 'strings'
        },
    }

    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self._hashable_config = ['hideable', 'validateAs', 'options',
            'label']

        self.set_default_config(self.defaults)
        assert self.config['returns']['type'] in ['strings', 'ordinals'], (
            'the "returns" type key must be one of ["strings", "ordinals"] '
            'not %s' % self.config['returns'])

        self.options = self.config['options']
        self._value = self.config['defaultValue']
        self.options_changed = Communicator()

    def set_value(self, new_value):
        if isinstance(new_value, int):
            assert new_value >= -1, 'Dropdown index must be >= -1, not %s' % new_value
            assert new_value <= len(self.options), 'Dropdown index must exist'
        elif isinstance(new_value, basestring):
            assert new_value in self.options, 'Value not in options %s' % self.options
        else:
            raise AssertionError(('Dropdown value type not '
                                  'recognized: {ctype}').format(ctype=type(new_value)))

        LabeledPrimitive.set_value(self, new_value)

    def set_options(self, options_list, new_value=None):
        if self.options != options_list:
            self.options = options_list

            try:
                if new_value is None:
                    self._value = self.config['defaultValue']
                else:
                    self._value = new_value
            except (AssertionError, ValueError) as error:
                # Default value must be a valid index into the new options
                # list or must be a string in that list.  If this is not the
                # case, then we'll reset the index to -1 (unset).
                self.set_value(-1)
            self.options_changed.emit(options_list)

    def current_index(self):
        """Return the current index (an int) of the dropdown."""
        if isinstance(self._value, int):
            return self._value

        try:
            return self.options.index(self._value)
        except ValueError:
            raise ValueError('Dropdown value {value} is not in {list}'.format(
                value=self._value, list=self.options))

    def value(self):
        # if there are no options to select or the user has not selected an
        # option, return None.
        if len(self.options) == 0 or self._value == -1:
            return None

        # get the value of the currently selected option.
        return_option = self.config['returns']['type']
        if return_option == 'strings':
            if isinstance(self._value, int):
                return_value = self.options[self._value]
            else:
                return_value = self._value
        else:
            return_value = self._value

        try:
            return self.config['returns']['mapValues'][return_value]
        except KeyError:
            # If the user's config doesn't have 'mapValues' OR the config
            # doesn't define a mapping for this value, return the original
            # return value, defined by the config['returns']['type'] string.
            return return_value

    def state(self):
        state_dict = {
            'value': self._value,  # always return the current index
            'is_hidden': self.is_hidden()
        }
        return state_dict


class TableDropdown(Dropdown):
    defaults = {
        'options': ['No options specified'],
        'defaultValue': 0,
        'validateAs': {'type': 'disabled'},
        'enabled': False,  # disable by default, until enabled.
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
            'type': 'strings'
        },
    }
    def __init__(self, configuration):
        Dropdown.__init__(self, configuration)
        self.set_default_config(self.defaults)

    def load_columns(self, filepath):
        raise NotImplementedError

    def state(self):
        state_dict = {
            'current_index': self.current_index(),
            'current_text': self.options[self.current_index()],
            'is_hidden': self.is_hidden(),
        }
        return state_dict

    def set_state(self, state_dict):
        self.set_value(state['current_text'])
        self.set_hidden(state['is_hidden'])


class OGRFieldDropdown(TableDropdown):
    defaults = {
        'options': ['No options specified'],
        'defaultValue': 0,
        'validateAs': {'type': 'disabled'},
        'enabled': False,  # disable by default, until enabled.
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
            'type': 'strings'
        },
    }
    def __init__(self, configuration):
        TableDropdown.__init__(self, configuration)
        self.set_default_config(self.defaults)

    def load_columns(self, filepath):
        from osgeo import ogr
        vector = ogr.Open(filepath)
        if not vector:
            self.set_options([])
            return

        layer = vector.GetLayer()
        fieldnames = [field.GetName() for field in layer.schema]
        print 'FIELDNAMES', fieldnames
        self.set_options(fieldnames, new_value=self.config['defaultValue'])


class Text(LabeledPrimitive):
    defaults = {
        'width': 60,
        'defaultValue': '',
        'validateAs': {'type': 'string'},
        'enabled': True,
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self._value = u""
        self.set_default_config(self.defaults)

        # Set the value of the element from the config's defaultValue.
        self.set_value(self.config['defaultValue'])

    def set_value(self, new_value):
        """Subclassed from LabeledPrimitive.set_value.  Casts all input values
        to utf-8.

            new_value - a python string.

        Returns nothing."""

        # Numbers must first be cast to a str before they can be converted to
        # python unicode objects.
        if isinstance(new_value, float) or isinstance(new_value, int):
            new_value = str(new_value)

        try:
            new_value = unicode(new_value, 'utf-8')
        except TypeError:
            # For when new_value is already unicode.
            pass

        LabeledPrimitive.set_value(self, new_value)

    def has_input(self):
        if len(self.value()) > 0:
            return True
        return False

class File(Text):
    defaults = {
        'validateAs': {'type': 'file'},
        'defaultValue': u'',
        'width': 60,
        'enabled': True,
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        Text.__init__(self, configuration)

        self.set_default_config(self.defaults)
        self.set_value(self.config['defaultValue'])

    def set_value(self, new_value):
        """Set the value of the File element.  All input values will be cast to
        UTF-8.

        new_value = a string, either a bytestring or unicode string.

        If new_value is relative to '~' (representing the user's home folder),
        the path will be expanded to be the absolute path of the value.
        Example: '~/some_file.txt' on linux might become
        '/home/username/some_file.txt'.  See the documentation for
        os.path.expanduser() for details about how this path is expanded.

        If the new value is a relative path (such as '../some_file.txt' or even
        just '.', indicating the current working directory), it will be expanded
        to be an absolute path based on the current working directory.

        NOTE: If you would like to clear the value of the field, use
        new_value=''.

        Returns nothing."""

        assert type(new_value) in [StringType, UnicodeType], ('New value must'
            'be either a bytestring or a unicode string, '
            '%s found.' % type(new_value))

        new_value = utils.decode_string(new_value)

        if new_value == '':
            # os.path.abspath('') is the same as os.getcwd(),
            # so I need to have a special case here.  If the user enters '.',
            # then the current dir will be used.
            absolute_path = ''
        else:
            absolute_path = os.path.abspath(os.path.expanduser(new_value))
        Text.set_value(self, absolute_path)


class Folder(File):
    defaults = {
        'validateAs': {'type': 'folder'},
        'defaultValue': u'',
        'width': 60,
        'enabled': True,
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }


class Static(Primitive):
    def __init__(self, configuration):
        Primitive.__init__(self, configuration)
        self._hashable_config = ['returnValue']
        new_defaults = {
            'returnValue': None,
        }

        self.set_default_config(new_defaults)

    def value(self):
        try:
            return self.config['defaultValue']
        except:
            pass
        return self.config['returnValue']

    def should_return(self):
        if 'args_id' in self.config:
            # Static elements should always return, so long as there's an
            # args_id.
            return True
        return False

    def state(self):
        return None

    def set_state(self, state):
        pass

    def is_valid(self):
        return True


class Label(Static):
    STYLE_ALERT_GREEN = {
        'padding': '15px',
        'background-color': '#d4efcc',
        'border': '2px solid #3e895b',
    }
    STYLE_ALERT_RED = {
        'padding': '15px',
        'background-color': '#ebabb6',
        'border': '2px solid #a23332',
    }
    STYLE_ALERT_BLUE = {
        'padding': '15px',
        'background-color': '#62C5E4',
        'border': '2px solid #005874',
    }
    STYLE_ALERT_YELLOW = {
        'padding': '15px',
        'background-color': '#faa732',
        'border': '2px solid #fbee50',
    }

    def __init__(self, configuration):
        Static.__init__(self, configuration)
        new_defaults = {
            'style': None,
            'label': ''
        }
        self.set_default_config(new_defaults)

        self._label = self.config['label']
        self._styles = self.config['style']
        self.label_changed = Communicator()
        self.styles_changed = Communicator()

    def label(self):
        return self._label

    def set_label(self, new_label):
        if self._label != new_label:
            self._label = new_label
            self.label_changed.emit(new_label)

    def styles(self):
        return self._styles

    def set_styles(self, new_styles):
        assert type(new_styles) == dict, ('new_styles must be a dict, not a '
                                          '%s') % type(new_styles)

        if new_styles != self._styles:
            self._styles = new_styles
            self.styles_changed.emit(new_styles)

    def state(self):
        return

    def set_state(self, state):
        pass

class CheckBox(LabeledPrimitive):
    defaults = {
        'label': u'',
        'validateAs': {'type': 'disabled'},
        'hideable': False,
        'enabled': True,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self._value = False  # initialize to be unchecked.

    def set_value(self, new_value):
        assert type(new_value) is BooleanType, ('new_value must be either True'
            ' or False, %s found' % type(new_value))
        LabeledPrimitive.set_value(self, new_value)

    def has_input(self):
        return self.value()

class Group(Element):
    def __init__(self, configuration, new_elements=None):
        Element.__init__(self, configuration)

        element_registry = {
            'file': File,
            'folder': Folder,
            'text': Text,
            'hidden': Static,
            'label': Label,
            'dropdown': Dropdown,
            'OGRFieldDropdown': OGRFieldDropdown,
            'container': Container,
            'checkbox': CheckBox,
            'multi': Multi,
            'tab': Tab,
            'tabGroup': TabGroup,
        }

        if new_elements is not None:
            element_registry.update(new_elements)

        self._registrar = element_registry
        self._elements = []
        new_defaults = {
            'enabled': True,
            'elements': [],
        }
        self.set_default_config(new_defaults)

        self.create_elements(self.config['elements'])
        self._display_label = True

    def _add_element(self, element):
        """Add the element to this group.

            element - an Element instance or subclass.

        Returns nothing."""
        self._elements.append(element)

    def create_elements(self, elements):
        """Create the elements contained by this group.

            elements - a list of dictionaries describing the elements to be
                created.

            Returns nothing."""
        for element_config in elements:
            try:
                new_element_cls = self._registrar[element_config['type']]
            except KeyError as error:
                raise KeyError('%s not recognized as an acceptable element type' % error)
            else:
                new_element = new_element_cls(element_config)

            self._add_element(new_element)

    def elements(self):
        return self._elements

    def set_enabled(self, new_state):
        """Enable or disable this Group.  Disables all elements in the group
        as well as the Group itself.

        new_state - A boolean.  If True, enable this element.  If False, disable
            this element.

        If the enabled state of this element changes, the interactivity_changed
        signal is emitted with the new state.

        Returns nothing."""

        assert type(new_state) is BooleanType, ('New state must be a boolean, '
            '%s found instead.' % new_state.__type__.__name__)

        for element in self.elements():
            element.set_enabled(new_state)

        Element.set_enabled(self, new_state)

    def set_visible(self, new_visibility):
        """Set the visibility of this Group and all its sub_elements.

        new_visibility - a boolean.  If True, mark this element as visible.  If
            False, mark as invisible.  Applies to all sub-elements.

        Returns nothing."""

        assert type(new_visibility) is BooleanType, ('Visibility must be True'
            'or False, %s found' % type(new_visibility))

        for element in self.elements():
            element.set_visible(new_visibility)

        Element.set_visible(self, new_visibility)

    def state(self):
        """Returns a python dictionary with the relevant state of the Group (not
            including contained elements)."""
        state_dict = {
            'enabled': self.is_enabled(),
        }
        return state_dict

    def set_state(self, state):
        """Set the state of this group element.

            state - a python dictionary with these attributes;
                'enabled' -> a boolean
        """
        self.set_enabled(state['enabled'])

class Container(Group):
    """A Container is a special kind of Group that can enable or disable all its
    sub-elements."""
    def __init__(self, configuration, new_elements=None):
        Group.__init__(self, configuration, new_elements)
        new_defaults = {
            'enabled': True,
            'label': '',
            'collapsible': False,
            'defaultValue': True,
        }
        self.set_default_config(new_defaults)

        self._collapsible = self.config['collapsible']
        self._collapsed = not self.config['defaultValue']

        self.toggled = Communicator()

        try:
            self.set_collapsed(self._collapsed)
        except InteractionError:
            # When the container is not collapsible
            pass

    def is_satisfied(self):
        if self.is_enabled():
            if self.is_collapsible() and not self.is_collapsed():
                return True
            elif not self.is_collapsible():
                return True
        return False

    def emit_signals(self):
        self.toggled.emit(self.is_collapsed())
        Group.emit_signals(self)

    def set_display_label(self, display):
        assert type(display) is BooleanType, 'display must be True or False'
        self._display_label = display

    def label(self):
        if self._display_label:
            return self.config['label']
        return ''

    def value(self):
        return not self._collapsed

    def set_collapsed(self, is_collapsed):
        assert type(is_collapsed) is BooleanType

        # can only set as collapsed if container is collapsible
        if not self.is_collapsible():
            raise InteractionError("Container is not collapsible")

        self._collapsed = is_collapsed
        self.toggled.emit(is_collapsed)

        for element in self.elements():
            element.set_enabled(not is_collapsed)
            element.set_visible(not is_collapsed)

    def is_collapsible(self):
        return self._collapsible

    def is_collapsed(self):
        return self._collapsed

    def state(self):
        """Returns a python dictionary with the relevant state of the Group (not
            including contained elements)."""
        state_dict = Group.state(self)
        state_dict['collapsed'] = self.is_collapsed()
        return state_dict

    def set_state(self, state):
        """Set the state of this group element.

            state - a python dictionary with these attributes;
                'enabled' -> a boolean
                'collapsed' -> a boolean
        """
        if self.is_collapsible():
            self.set_collapsed(state['collapsed'])
        Group.set_state(self, state)

    def is_valid(self):
        """A group is always valid."""
        return True

    def should_return(self):
        LOGGER.debug('Checking whether should return: %s', self)
        # if element does not have an args_id, we're not supposed to return.
        # Therefore, return False.
        if 'args_id' not in self.config:
            LOGGER.debug('Element %s does not have an args_id', self)
            return False

        # If none of the previous conditions have been met, return True.
        return True

    def is_required(self):
        # containers are never reauired.
        return False


class Multi(Container):
    def __init__(self, configuration, new_elements=None):
        Container.__init__(self, configuration, new_elements)
        new_defaults = {
            'label': '',
            'enabled': True,
            'collapsible': False,
            'defaultValue': True,
            'link_text': 'Add another',
            'helpText': "",
            'return_type': 'list',
            'template': {
                'type': 'text',
                'label': 'Input a number',
                'validateAs': {'type': 'disabled'},
            },
        }

        # clean up unused configuration options inherited from Container
        # we have absolutely no interest in user-defined elements, since this
        # element only has elements created according to the template.
        # If any elements happen to have been created by the user, remove them
        # and log a warning.
        if len(self._elements) > 0:
            self._elements = []
            LOGGER.warn('Multi element does not currently support '
                ' non-template elements.  Elements found have been removed.')

        self.set_default_config(new_defaults)

        self.element_added = Communicator()
        self.element_removed = Communicator()

    def emit_signals(self):
        for element_index in range(len(self._elements)):
            self.element_added.emit(new_index)

    def add_element(self, index=None):
        # need an optional argument for when an element is added by the
        # Container widget.
        self.create_elements([self.config['template']])
        new_index = len(self.elements()) - 1
        LOGGER.debug('Adding a new element at index %s', new_index)
        self.element_added.emit(new_index)  #index of element

    def remove_element(self, index):
        popped_element = self._elements.pop(index)
        self.element_removed.emit(index)

    def set_value(self, value_list):
        for value in value_list:
            self.add_element()
            self.elements()[-1].set_value(value)

    def value(self):

        return_type = self.config['return_type']
        return_values = {
            'list': lambda elem_list: [_recursive_value(e) for e in elem_list],
            'dict': lambda elem_list: dict((e.config['args_id'],
                _recursive_value(e)) for e in elem_list),
        }

        def _recursive_value(element):
            """Recurse through a nested set of elements and return a list of
            values and lists of values for the elements contained within this
            multi."""
            if isinstance(element, Container):
                # may raise KeyError in either of two circumstances:
                #  - args_id is missing from any of the contained elements
                #  - return_value is not in ['list', 'dict']
                value = return_values[return_type](element.elements())
            else:
                value = element.value()
            return value

        return [_recursive_value(e) for e in self.elements()]

    def state(self):
        state_dict = Container.state(self)
        state_dict['value'] = self.value()
        return state_dict

    def set_state(self, state):
        self.set_value(state['value'])
        Container.set_state(self, state)

class TabGroup(Group):
    def create_elements(self, elements):
        """Create elements after first asserting that all contained elements
        are tabs."""
        for element_config in elements:
            assert element_config['type'] == 'tab', ('Element type must be '
                '"tab", %s found instead' % element_config['type'])
        Group.create_elements(self, elements)

class Tab(Group):
    def __init__(self, configuration, new_elements=None):
        Group.__init__(self, configuration, new_elements)
        new_defaults = {
            'enabled': True,
            'label': '',
        }
        self.set_default_config(new_defaults)

    def label(self):
        return self.config['label']

# The form class represents a single-window form where the user enters various
# inputs and then does something with them.  The IUI ModelUI would be an example
# of a form.
# Defining characteristics of a Form:
#  * contains a group of elements
#  * packages up required arguments from elements
#  * starts a model running when triggered.
class Form():
    def __init__(self, configuration):
        self._ui = Group(configuration)

        self.elements = self.find_elements()
        self.runner = None
        self._runner_class = execution.PythonRunner
        self._unknown_signals = []  # track signals we might setup later
        self.langs = []  # initially, available langs are unknown.

        self.setup_communication(self.elements)

        self.submitted = Communicator()

        # now that the form has been created, load the lastrun state, if
        # appliccable.
        lastrun_uri = self.lastrun_uri()
        try:
            self.load_state(lastrun_uri)
            LOGGER.info('Successfully loaded lastrun from %s',
                lastrun_uri)
        except IOError:
            # when no lastrun file exists for this version
            LOGGER.warn('No lastrun file found at %s.  Skipping.',
                lastrun_uri)

    def set_langs(self, langs):
        """Set the available languages of the form."""
        self.langs = langs

    def get_target_workspace(self):
        """Fetch the folder that should be opened for the user once the model
        finishes execution.

        There are multiple ways that this value is set (in order of priority):
            1. If config['openDirOnComplete'] is set and formatted properly
            2. There is an element with an args_id of 'workspace_dir'
            3. If none of the above are satisfied, returns the user's home dir.
        """
        try:
            # does openDirOnComplete exist?
            user_dirconfig = self._ui.config['openDirOnComplete']
            if user_dirconfig['type'] == 'element':
                elem_id = user_dirconfig['id']
                workspace_dir_elem = self.element_index[elem_id]
                return workspace_dir_elem.value()
            else:
                # assume type is folder, which should be set by the user
                return user_dirconfig['path']
        except KeyError:
            # Check if an element with args_id workspace_dir exists
            for elem_id, element in self.element_index.iteritems():
                if element.config['args_id'] == 'workspace_dir':
                    return element.value()

        # Base case: return home dir.
        return os.path.expandpath('~')

    @property
    def element_index(self):
        return dict((e.get_id('user'), e) for e in self.elements)

    def emit_signals(self):
        for element in self.elements:
            element.emit_signals()

    def setup_communication(self, elements_list):
        """Set up communication between elements for all elements in the
        elements_list.  Returns nothing."""
        for element in elements_list:
            if 'signals' in element.config:
                self._setup_element_communication(element)

    def find_element(self, id):
        return self.element_index[id]

    def _setup_element_communication(self, element):
        # Two varieties of signal are permitted:
        #
        # Short-form signals are strings in the form:
        #    <simplified_signalname>:<target_element_id>
        # Implemented shortform signals:
        #  "enables" - indicates that the target element should be enabled
        #       when this element's satisfied.
        #
        # Long-form signals are dictionaries in this form:
        # {
        #   "signal_name": "<string name of the signal>",
        #   "target": one of several target forms, documented below.
        # }
        #
        requested_signals = utils.get_valid_signals(element.config['signals'],
            element.signals)

        # having asserted that all signals in requested_signals are known, we
        # can try to connect the communicators to their targets.
        # TARGET FORMS:
        #    element notation: Element:<element_id>.func_name
        #    python notation: Python:package.module.function

        for signal_config in requested_signals:
            self._setup_signal(signal_config, element)

    def _setup_signal(self, signal_config, src_element):
        LOGGER.debug('Setting up signal %s.%s -> %s',src_element.get_id('user'),
            signal_config['signal_name'], signal_config['target'])
        try:
            signal_name, target_func = utils.setup_signal(signal_config,
                self.element_index)

            # connect the target signal.
            # TODO: specify what data should be passed as an argument?
            getattr(src_element, signal_config['signal_name']).register(target_func)
        except KeyError:
            # when the target element is not known, add the element's
            # config to the config_later set so we can try them out later.
            LOGGER.debug('Signal %s.%s -> %s failed.  Element not known',
                src_element.get_id('user'), signal_config['signal_name'],
                signal_config['target'])
            self._unknown_signals.append((signal_config, src_element))

    def add_element(self, element):
        """Add an element to this form, registering all element callbacks and
        inter-element communication as necessary.

            element - an element instance to add to this form

        Returns nothing."""
        LOGGER.debug('Ading element "%s" to the form', element.get_id('user'))

        if 'signals' in element.config:
            self._setup_element_communication(element)

        self._ui._add_element(element)
        self.elements.append(element)

        # attempt to process unknown signals.
        self._process_unknown_signals()

    def _process_unknown_signals(self):
        """check if there are any signals that need to be processed and set
        them up accordingly."""

        # make a copy of the currently unknown signals, and reset the local
        # attribute to be empty so that we process the current state of signals
        # and not mix up the two.
        currently_unknown_signals = self._unknown_signals
        self._unknown_signals = []

        for unknown_signal, src_element in currently_unknown_signals:
            self._setup_signal(unknown_signal, src_element)

    def title(self):
        """Return the title string, if it's defined in the configuration.
        Returns None if no title is defined."""
        try:
            return self._ui.config['label']
        except KeyError:
            LOGGER.debug('No form title defined')
            return None

    def find_elements(self):
        """Recurse through all elements in this Form's UI and locate all Element
        objects.

        Returns a list of element object references."""

        # TODO: if two elements have the same ID, raise an exception with a
        # helpful error message.
        all_elements = []

        def append_elements(element_list):
            for element in element_list:
                if isinstance(element, Group):
                    if isinstance(element, Container):
                        all_elements.append(element)
                    append_elements(element._elements)
                else:
                    all_elements.append(element)

        append_elements(self._ui._elements)
        return all_elements

    def collect_arguments(self):
        """Collect arguments from all elements in this form into a single
        dictionary in the form of {'args_id': value()}.  If an element does not
        have an args_id attribute, it is skipped.  Likewise, if an element
        should not be returned (if its should_return() function returns False),
        the element is skipped.

        Returns a python dictionary."""

        # Create the args dictionary and pass it back to the Application.
        args_dict = {}
        for element in self.elements:
            if element.should_return():
                args_dict[element.config['args_id']] = element.value()
            else:
                try:
                    args_id = element.config['args_id']
                except KeyError:
                    args_id = element.get_id('user')
                LOGGER.debug('Element %s should not return, skipping args_id %s',
                    element, args_id)
        return args_dict

    def save_state(self, uri):
        """Assemble the state of all elements and save them to a json object.

            uri - a URI to the file where the dictionary should be saved as JSON

            Returns nothing."""
        state_dict = {}
        for element in self.elements:
            element_id = element.get_id()
            element_state = element.state()
            try:
                element_state['_debug'] = element._get_hashable_config()
            except TypeError:
                # happens when element_state is None, which can happen when the
                # element is not a primitive.
                pass

            state_dict[element_id] = element_state

        utils.save_dict_to_json(state_dict, uri, 4)

    def load_state(self, state_uri):
        """Load a state from a file on disk.

            state_uri - a URI to a file on disk from where the Form's state can
                be loaded.

            Returns nothing."""
        form_state = utils.load_json(state_uri)
        for element in self.elements:
            element_id = element.get_id()

            # get the state of the element that matches this ID.
            try:
                element_state = form_state[element_id]
                element.set_state(element_state)
            except KeyError as missing_key:
                # When an ID key is missing, it means that the developer added
                # an element or else changed the element enough for it to not be
                # recognizeable to palisades.  When this happens, we can't set
                # the state, so log a warning and proceed.
                LOGGER.warn('Element ID %s (%s) does not have a saved state.',
                    missing_key, element.get_id('user'))

    def lastrun_uri(self):
        """Fetch the URI for the internal lastrun save file."""
        version = palisades.__version__
        if not re.match('([0-9].){3}', version):
            version_str = 'dev'
        else:
            version_str = version
        lastrun_filename = '%s_lastrun_%s.json' % (self._ui.config['modelName'],
            version_str)

        lastrun_uri = os.path.join(palisades.utils.SETTINGS_DIR, lastrun_filename)
        LOGGER.debug('Lastrun URI: %s', lastrun_uri)
        return lastrun_uri

    def form_is_valid(self):
        """Check if all the inputs in this form are valid.  Returns True if so,
        a list of tuples if not.  Tuples indicate failed"""
        # Check the validity of all inputs
        form_data = []
        for element in self.elements:
            try:
                form_data.append((element.config['args_id'], element.is_valid(),
                    element.should_return(), element.is_required(),
                    element.is_visible(), element.value()))
            except KeyError:
                # no attribute args_id, so skip.
                pass


        def element_ok_for_submission(args_id, is_valid, should_return,
                is_required, is_visible, value):
            """Check that this element is ok for submission.  Returns a
            boolean."""
            if not is_visible:
                return True
            if not is_valid and is_required:
                return False
            if not should_return:  # element should not return, so ignore
                return True
            if is_valid and should_return is True: # is valid, should return
                return True
            return False  # otherwise, element should not return

        element_validity = map(lambda x: element_ok_for_submission(*x),
            form_data)

        #print "VALID | args_id, is_valid, should_return, is_required, is_visible"
        #for element, valid in zip(form_data, element_validity):
        #    print valid, element

        return not False in element_validity

    def form_errors(self):
        """Return a list of tuples containing (args_id, value) that are invalid
        values."""
        invalid_inputs = []
        for element in self.elements:
            if not element.is_visible():
                continue  # skip elements that are hidden from view.

            if not element.is_valid():
                invalid_inputs.append((element.config['args_id'], element.value()))
        return invalid_inputs

    def save_to_python(self, filename):
        """Save the form's data to an exacuteable python file at filename"""
        if not self.form_is_valid():
            raise InvalidData(self.form_errors())
        else:
            try:
                function_name = self._ui.config['targetFunction']
            except KeyError:
                function_name = 'execute'
            file_path = self._ui.config['targetScript']

            fileio.save_model_run(self.collect_arguments(), file_path,
                    filename, function_name)

    def set_runner(self, runner_class):
        """Set the runner class that should be used for this form.
        Runner_class should provide the same interface as and similar
        functionality to execution.PythonRunner."""
        self._runner_class = runner_class

    def submit(self, event=None):
        LOGGER.debug('Starting the form submission process')

        # if success, assemble the arguments dictionary and send it off to the
        # base Application
        if not self.form_is_valid():
            raise InvalidData(self.form_errors())
        else:
            # save the current state of the UI to the lastrun location.
            self.save_state(self.lastrun_uri())

            args_dict = self.collect_arguments()

            # TODO: submit the args dict and other relevant data back to app.
            try:
                try:
                    function_name = self._ui.config['targetFunction']
                except KeyError:
                    function_name = 'execute'

                self.runner = self._runner_class(self._ui.config['targetScript'],
                    args_dict, function_name)
                self.submitted.emit(True)
            except ImportError as error:
                LOGGER.error('Problem loading %s', self._ui.config['targetScript'])
                raise

            self.runner.start()


