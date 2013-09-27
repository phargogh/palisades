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

class Element(core.Communicator):
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
