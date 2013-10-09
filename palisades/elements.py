import os
import threading
import logging

import palisades
from palisades import fileio
from palisades import ui
from palisades import core
from palisades import validation
from palisades import executor

from PyQt4 import QtGui

DISPLAYS = {
    'Qt': ui
}


UI_LIB = ui
LOGGER = logging.getLogger('elements')

# Assume this is a window for a moment.
class Application(object):
    def __init__(self, config_uri):
        configuration = fileio.read_config(config_uri)
        self._window = Form(configuration)

class Element():
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
        self.config_changed = core.Communicator()
        self.interactivity_changed = core.Communicator()

        # Render the configuration and save to self.config
        self.config = core.apply_defaults(configuration, self._default_config)

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
        self.config = core.apply_defaults(self.config, self._default_config)
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
    def __init__(self, configuration):
        Element.__init__(self, configuration)
        self._value = None
        self._valid = False  # Assume invalid until proven otherwise
        self._validation_error = None

        # Set up our Communicator(s)
        self.value_changed = core.Communicator()

        # update the default configuration
        new_defaults = {
            'validateAs': {'type': 'disabled'}
        }
        self.set_default_config(new_defaults)

        # Set up our validator
        self._validator = validation.Validator(
            self.config['validateAs']['type'])

    def set_value(self, new_value):
        """Set the value of this element.  If the element's value changes, all
        registered callbacks will be emitted.

        Returns nothing."""

        if not self.is_enabled():
            return

        # If the value of this element has changed, we want to trigger all the
        # elements that requested notification.
        old_value = self.value()
        if old_value != new_value:
            self._value = new_value
            self._valid = False
            self.value_changed.emit(new_value)
            self.validate()

    def value(self):
        """Get the value of this element."""
        return self._value

    def is_valid(self):
        """Return the validity of this input.  If the element has not been
        validated, False will be returned.

        NOTE: If this function is called while validation is in progress, False
        will always be returned.
        """
#TODO: fix this behavior so that it makes sense.
        return self._valid

    def validate(self):
        validation_dict = self.config['validateAs']
        validation_dict['value'] = self.value()
        self._validator.validate(validation_dict)  # this starts the thread

        # start a thread here that checks the status of the validator thread.
        # TODO: Timer is a one-shot execution.  Make a repeating Timer.
        self.timer = threading.Timer(0.1, self.check_validator)
        self.timer.start()

    def check_validator(self):
        if self._validator.thread_finished():
            self.timer.cancel()  # stop the timer thread
            error, state = self._validator.get_error()

            self._valid = state
            self._validation_error = error


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
        absolute_path = os.path.abspath(os.path.expanduser(new_value))
        Text.set_value(self, absolute_path)

ELEMENTS = {
    'file': File,
    'folder': File,
    'text': Text
}

class Group(Element):
    def __init__(self, configuration, registrar=ELEMENTS):
        Element.__init__(self, configuration)
        self._registrar = registrar
        self._elements = []
        new_defaults = {
            'elements': []
        }
        self.set_default_config(new_defaults)

        self.create_elements(self.config['elements'])

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
        form_is_valid = False in [e[0] for e in form_data]

        # if success, assemble the arguments dictionary and send it off to the
        # base Application
        if not form_is_valid:
            print 'Form has invalid inputs.  Check your inputs and try again.'
            # get the invalid inputs
            print form_data

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


