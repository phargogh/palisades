import os
import threading
import logging
from types import *

from palisades import fileio
from palisades import utils
from palisades.utils import Communicator
from palisades import validation
from palisades import execution
import palisades.gui


LOGGER = logging.getLogger('elements')

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
    def __init__(self, config_uri):
        # if GUI is None, have to visual display.
        configuration = fileio.read_config(config_uri)
        self._window = Form(configuration)

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
    def __init__(self, configuration, parent=None):
        object.__init__(self)
        self._enabled = True
        self._parent_ui = parent
        self._default_config = {}

        # Set up the communicators
        self.config_changed = Communicator()
        self.interactivity_changed = Communicator()

        # Render the configuration and save to self.config
        self.config = utils.apply_defaults(configuration, self._default_config)

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

        self._default_config.update(new_defaults)
        self.config = utils.apply_defaults(self.config, self._default_config)
        self.config_changed.emit(self.config)

    def is_enabled(self):
        """Query whether this element is enabled, indicating whether this
        element can be interacted with by the user.

        Returns a boolean."""

        return self._enabled

    def set_enabled(self, new_state):
        """Enable or disable this element.

        new_state - A boolean.  If True, enable this element.  If False, disable
            this element.

        If the enabled state of this element changes, the interactivity_changed
        signal is emitted with the new state.

        Returns nothing."""

        new_state = bool(new_state)

        if new_state != self._enabled:
            self._enabled = new_state
            self.interactivity_changed.emit(new_state)

class Primitive(Element):
    """Primitive represents the simplest input element."""
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

        # Set up our Communicator(s)
        self.value_changed = Communicator()
        self.validation_completed = Communicator()

        # update the default configuration
        new_defaults = {
            'validateAs': {'type': 'disabled'}
        }
        self.set_default_config(new_defaults)

        # Set up our validator
        self._validator = validation.Validator(
            self.config['validateAs']['type'])
        self._validator.finished.register(self._get_validation_result)

    def set_value(self, new_value):
        """Set the value of this element.  If the element's value changes, all
        registered callbacks will be emitted.

        Returns nothing."""

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
            self._validator.join()

        # Return whether validation passed (a boolean).
        return self._valid

    def validate(self):
        # if validation is already in progress, block until finished.
        while not self._validator.thread_finished():
            pass

        validation_dict = self.config['validateAs']
        validation_dict['value'] = self.value()
        self._validator.validate(validation_dict)  # this starts the thread

    def _get_validation_result(self, error):
        """Utility class method to get the error result from the validator
        object.  Sets self._valid according to whether validation passed or
        failed, and sets the validation error to the error found (if any).

        error - a tuple of (error_msg, error_state)."""
        error_msg, state = error

        if state == validation.V_PASS:
            self._valid = True
        else:
            self._valid = False

        self._validation_error = error_msg
        print 'validation completed'
        self.validation_completed.emit(error)


class LabeledPrimitive(Primitive):
    def __init__(self, configuration):
        Primitive.__init__(self, configuration)

        new_defaults = {
            'label': u""
        }
        self.set_default_config(new_defaults)
        self._label = self.config['label']

    def set_label(self, new_label):
        cast_label = new_label.decode("utf-8")
        self._label = cast_label

    def label(self):
        return self._label

class Dropdown(LabeledPrimitive):
    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        new_defaults = {
            'options': ['No options specified'],
            'defaultValue': 0,
            'returns': 'strings',
        }
        self.set_default_config(new_defaults)
        assert self.config['returns'] in ['strings', 'ordinals'], (
            'the "returns" key must be either "strings" or "ordinals", '
            'not %s' % self.config['returns'])

        self.options = self.config['options']
        self._value = self.config['defaultValue']

    def set_value(self, new_value):
        assert type(new_value) is IntType, 'Dropdown index must be an int'
        assert new_value >= 0, 'Dropdown index must be >= 0'
        assert new_value < len(self.options), 'Dropdown index must exist'
        LabeledPrimitive.set_value(self, new_value)

    def current_index(self):
        """Return the current index (an int) of the dropdown."""
        return self._value

    def value(self):
        # if there are no options to select or the user has not selected an
        # option, return None.
        if len(self.options) is 0 or self._value is -1:
            return None

        # get the value of the currently selected option.
        return_option = self.config['returns']
        if return_option is 'strings':
            return self.options[self._value]
        else:  # return option is 'ordinals'
            return self._value

class Text(LabeledPrimitive):
    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self._value = u""

        new_defaults = {
            'width': 60,
            'defaultValue': '',
            'validateAs': {'type': 'string'},
        }
        self.set_default_config(new_defaults)

        # Set the value of the element from the config's defaultValue.
        self.set_value(self.config['defaultValue'])

    def set_value(self, new_value):
        """Subclassed from LabeledPrimitive.set_value.  Casts all input values
        to utf-8.

            new_value - a python string.

        Returns nothing."""

        cast_value = unicode(new_value).decode('utf-8')
        LabeledPrimitive.set_value(self, cast_value)

class File(Text):
    def __init__(self, configuration):
        Text.__init__(self, configuration)
        new_defaults = {
            'validateAs': {'type': 'file'},
        }
        self.set_default_config(new_defaults)

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

        if new_value == '':
            # os.path.abspath('') is the same as os.getcwd(),
            # so I need to have a special case here.  If the user enters '.',
            # then the current dir will be used.
            absolute_path = ''
        else:
            absolute_path = os.path.abspath(os.path.expanduser(new_value))
        Text.set_value(self, absolute_path)

class Static(Element):
    def __init__(self, configuration):
        Element.__init__(self, configuration)
        new_defaults = {
            'returns': None
        }

        self.set_default_config(new_defaults)

    def value(self):
        return self.config['returns']

class Label(Static):
    def __init__(self, configuration):
        Static.__init__(self, configuration)
        new_defaults = {
            'label': ''
        }
        self.set_default_config(new_defaults)

    def label(self):
        return self.config['label']



class Group(Element):
    def __init__(self, configuration, new_elements=None):
        Element.__init__(self, configuration)

        element_registry = {
            'file': File,
            'folder': File,
            'text': Text,
            'hidden': Static,
            'label': Label,
            'dropdown': Dropdown,
            'container': Container,
        }

        if new_elements is not None:
            element_registry.update(new_elements)

        self._registrar = element_registry
        self._elements = []
        new_defaults = {
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
            new_element = self._registrar[element_config['type']](element_config)
            LOGGER.debug('Creating new element %s', new_element)

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

class Container(Group):
    """A Container is a special kind of Group that can enable or disable all its
    sub-elements."""
    def __init__(self, configuration, new_elements=None):
        Group.__init__(self, configuration, new_elements)
        new_defaults = {
            'label': 'Container',
            'collapsible': False,
        }
        self.set_default_config(new_defaults)

        self._collapsible = self.config['collapsible']
        self._collapsed = False

        self.toggled = Communicator()

    def set_display_label(self, display):
        assert type(display) is BooleanType, 'display must be True or False'
        self._display_label = display

    def label(self):
        if self._display_label:
            return self.config['label']
        return ''

    def set_collapsed(self, is_collapsed):
        assert type(is_collapsed) is BooleanType

        # can only set as collapsed if container is collapsible
        if not self.is_collapsible():
            raise InteractionError("Container is not collapsible")

        self._collapsed = is_collapsed
        self.toggled.emit(is_collapsed)

        for element in self.elements():
            element.set_enabled(not is_collapsed)

    def is_collapsible(self):
        return self._collapsible

    def is_collapsed(self):
        return self._collapsed

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

    def find_elements(self):
        """Recurse through all elements in this Form's UI and locate all Element
        objects.

        Returns a list of element object references."""

        all_elements = []

        def append_elements(element_list):
            for element in element_list:
                if isinstance(element, Group):
                    append_elements(element._elements)
                else:
                    all_elements.append(element)

        append_elements(self._ui._elements)
        return all_elements


    def submit(self):
        # Check the validity of all inputs
        form_data = [(e.is_valid(), e.value()) for e in self.elements]
        print form_data
        form_is_invalid = False in [e[0] for e in form_data]
        print form_is_invalid

        # if success, assemble the arguments dictionary and send it off to the
        # base Application
        if form_is_invalid:
            invalid_inputs = []
            for is_valid, value in form_data:
                if not is_valid:
                    invalid_inputs.append(value)

            raise InvalidData(invalid_inputs)
        else:
            # Create the args dictionary and pass it back to the Application.
            args_dict = {}
            for element in self.elements:
                try:
                    args_dict[element.config['args_id']] = element.value()
                except KeyError:
                    LOGGER.debug('Element %s does not have an args_id', element)

            print args_dict
            # TODO: submit the args dict and other relevant data back to app.
            try:
                self.runner = execution.PythonRunner(self._ui.config['targetScript'],
                    args_dict)
                self.runner.start()
            except ImportError as error:
                LOGGER.error('Problem loading %s', self._ui.config['targetScript'])
                raise


