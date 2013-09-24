from palisades import fileio
from palisades import ui
from palisades import core

ELEMENTS = {}
LAYOUT_VERTICAL = 0

DISPLAYS = {
    'Qt': ui.Qt4
}


# Assume this is a window for a moment.
class Application(object):
    def __init__(self, config_uri):
        configuration = fileio.read_config(config_uri)

class Element(core.Communicator):
    """The Element class is the base class of all palisades element.  It
    provides fundamental functionality shared by all elements."""
    _enabled = True
    _required = False

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



