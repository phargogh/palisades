import os
import threading

import palisades
from palisades import fileio
from palisades import ui
from palisades import core
from palisades import validation

from PyQt4 import QtGui

DISPLAYS = {
    'Qt': ui
}


UI_LIB = ui

# Assume this is a window for a moment.
class Application(object):
    _gui = ui.Application().app
    _window = None

    def __init__(self, config_uri):
        configuration = fileio.read_config(config_uri)
        self._window = Form(configuration)

    def run(self):
        self._window.show()
        self._gui.exec_()

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


class OldElement(core.Communicator):
    """The Element class is the base class of all palisades element.  It
    provides fundamental functionality shared by all elements."""
    _enabled = True
    _required = False
    _application = None
    _default_widget = None
    _gui_widget = None
    _default_config = {}

    def __init__(self, configuration):
        core.Communicator.__init__(self)
        configuration = core.apply_defaults(configuration, self._default_config)
        self.config = configuration

        # we only want to create this element's widget object if one is
        # specified
        if self._default_widget is not None:
            self._gui_widget = self._default_widget(configuration)

    def set_root(self, root_ptr):
        if not isinstance(root_ptr, Application):
            raise TypeError('Root class must be an elements.Application')
        self._application = root_ptr

    def _set_enabled(self, enabled):
        """Set the local, private attribute indicating whether this element is
        enabled.  All registered callbacks will be notified.

        Returns nothing."""

        self._enabled = enabled
        self.emit()

    def enable(self):
        """Enable the element.  Returns nothing,"""
        self._set_enabled(True)

    def disable(self):
        """Disable the element.  Returns nothing."""
        self._set_enabled(False)

    def is_enabled(self):
        """Check if the element is enabled.

        Returns a boolean."""

        return self._enabled

    def is_required(self):
        """Check if the element is required.

        Returns a boolean."""

        return self._required

    def widget(self):
        """Return the instance of the GUI Widget representing this element"""
        return self._gui_widget

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
            self.value_changed.emit(new_value)

    def value(self):
        """Get the value of this element."""
        return self._value

    def validate(self):
        validation_dict = self.config['validateAs']
        validation_dict['value'] = self.value()
        self._validator.validate(validation_dict)  # this starts the thread

        # start a thread here that checks the status of the validator thread.
        self.timer = threading.Timer(0.1, self.check_validator)
        self.timer.start()

    def check_validator(self):
        if self._validator.thread_finished():
            self.timer.cancel()  # stop the timer thread
            error, state = self._validator.get_error()

            self._valid = state
            self._validation_error = error


class OldPrimitive(Element):
    """The Primitive class is the base class for all elements that take user
    input."""

    _default_config = {
        'validateAs': {'type': 'disabled'}
    }

    def __init__(self, configuration):
        Element.__init__(self, configuration)
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
            self.widget().set_value(new_value)
            self.emit()

    def value(self):
        """Get the value of this element."""
        return self.widget().value()

    def validate(self):
        validation_dict = self.config['validateAs']
        validation_dict['value'] = self.value()
        self._validator.validate(validation_dict)  # this starts the thread

        # start a thread here that checks the status of the validator thread.
        self.timer = ui.Timer(0.1, self.check_validator)
        self.timer.start()

    def check_validator(self):
        if self._validator.thread_finished():
            self.timer.cancel()  # stop the timer thread
            error, state = self._validator.get_error()

            self.widget().set_error(error, state)


class LabeledPrimitive(Primitive):
    _label = u""
    _preferred_layout = palisades.LAYOUT_GRID

    def set_label(self, new_label):
        cast_label = new_label.decode("utf-8")
        self._label = cast_label
        self.widget().set_label(cast_label)

    def label(self):
        return self._label

class Text(LabeledPrimitive):
    _value = u""
    _default_widget = ui.Text
    _default_config = {
        'width': 60,
        'defaultValue': '',
        'validateAs': {'type': 'string'},
    }

    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self.set_value(configuration['defaultValue'])
        self.widget().set_callback(self.validate)

    def set_value(self, new_value):
        # enforce all strings to be utf-8
        cast_value = new_value.decode('utf-8')
        LabeledPrimitive.set_value(self, cast_value)
        self.widget().set_value(cast_value)

class File(Text):
    _default_widget = ui.File
    _default_config = {
        'width': 10000,  # effectively unlimitied.
        'defaultValue': '',
        'validateAs': {'type': 'file'},
    }

    def set_value(self, new_value):
        absolute_path = os.path.abspath(new_value)
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
        self._default_config = {
            'elements': []
        }
        self.create_elements(configuration['elements'])

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
            print new_element

            self._add_element(new_element)

class OldGroup(Element):
    """The Group class allows for elements to be grouped together."""

    _layout = palisades.LAYOUT_VERTICAL
    _registrar = ELEMENTS  # default element registrar
    _elements = []
    _gui_widget = None
    _default_widget = ui.Empty
    _default_config = {
        'elements': []
    }

    def __init__(self, configuration):
        Element.__init__(self, configuration)
        self.create_elements(configuration['elements'])

    def _add_element(self, element_ptr):
        """Add an element to this group's layout."""
        self._elements.append(element_ptr)
        self._gui_widget.add_element(element_ptr.widget())

    def create_elements(self, elements_configuration):
        """Creates elements belonging to this Group.

            elements_configuration - a list of dictionaries, where each
                dictionary contains information about the element.

            Returns nothing."""

        for element_config in elements_configuration:
            # Create the new element.  This creates the element with all of its
            # attributes, and even creates the Widget in memory with all of its
            # attributes.
            new_element = self._registrar[element_config['type']](element_config)
            print new_element

            # Add the newly created element to this group's Widget.
            self._add_element(new_element)

    def show(self):
        self._gui_widget.show()

class Form(Group):
    _registrar = ELEMENTS
    _elements = []
    _default_widget = ui.FormWindow
    _default_config = {
        'elements': [],
    }
