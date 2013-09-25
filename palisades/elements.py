from palisades import fileio
from palisades import ui
from palisades import core

ELEMENTS = {}
LAYOUT_VERTICAL = 0
LAYOUT_VERTICAL_LIST = 1
LAYOUT_HORIZONTAL_LIST = 2
LAYOUT_GRID = 3

DISPLAYS = {
    'Qt': ui.Qt4
}


UI_LIB = ui.Qt4()

# Assume this is a window for a moment.
class Application(object):
    _gui

    def __init__(self, config_uri):
        self._gui = ui.Qt4()
        configuration = fileio.read_config(config_uri)

class Element(core.Communicator):
    """The Element class is the base class of all palisades element.  It
    provides fundamental functionality shared by all elements."""
    _enabled = True
    _required = False
    _application
    _default_widget = UI_LIB.Empty
    _gui_widget
    _default_config = {}

    def __init__(self, configuration):
        core.Communicator.__init__(self)
        self._gui_widget = _default_widget(configuration)

    def _apply_defaults(self, configuration):
        """Take the input configuration and apply default values if the
        configuration option was not specified.

        configuration - a python dictionary of configuration options for this
            element.

        Returns a dictionary with rendered default values."""

        sanitized_config = configuration.copy()
        for key, default_value in self._default_config.iteritems():
            if key not in configuration:
                sanitized_config[key] = default_value

        return sanitized_config

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

    _value = None

    def set_value(self, new_value):
        """Set the value of this element.  If the element's value changes, all
        registered callbacks will be emitted.

        Returns nothing."""

        if not self.is_enabled():
            return

        old_value = self._value
        self._value = new_value

        # If the value of this element has changed, we want to trigger all the
        # elements that requested notification.
        if old_value != new_value:
            self.emit()

    def value(self):
        """Get the value of this element."""
        return self._value

class Group(Element):
    """The Group class allows for elements to be grouped together."""

    _layout = LAYOUT_VERTICAL_LIST
    _registrar = ELEMENTS  # default element registrar
    _elements = []
    _gui_widget

    def set_layout(self, layout = LAYOUT_VERTICAL_LIST):
        self._layout = layout

    def _add_element(self, element_ptr):
        """Add an element to this group's layout."""
        _elements.append(element_ptr)
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
            new_element = _registrar[element_config['type']](element_config)

            # Add the newly created element to this group's Widget.
            self._add_element(new_element)






class LabeledPrimitive(Primitive):
    _label = u""
    _preferred_layout = LAYOUT_GRID

    def set_label(self, new_label):
        cast_label = new_label.decode("utf-8")
        self._label = cast_label

    def label(self):
        return self._label

class Text(LabeledPrimitive):
    _value = u""

    def set_value(self, new_value):
        # enforce all strings to be utf-8
        cast_value = new_value.decode('utf-8')
        LabeledPrimitive.set_value(self, cast_value)

class File(Text):
    pass


