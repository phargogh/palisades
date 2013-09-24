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
    _value = None
    _enabled = True

    def set_value(self, new_value):
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

    def _set_enabled(self, enabled):
        self._enabled = enabled
        self.emit()

    def enable(self):
        self._set_enabled(True)

    def disable(self):
        self._set_enabled(False)

    def is_enabled(self):
        return self._enabled
