"""This file contains the core logic of the palisade package."""

LAYOUT_VERTICAL_LIST = 1
LAYOUT_HORIZONTAL_LIST = 2
LAYOUT_GRID = 3


class SignalNotFound(Exception):
    """A custom exception for when a signal was not found."""
    pass

class Communicator(object):
    """Element represents the base class for all UI elements.  It focuses
    on inter-element connectivity and communication."""
    # signals is a list of dictionaries
    # signal['target'] - a pointer to the signal's target element and function
    # signal['condition'] - the condition under which this signal is emitted
    # When a signal is emitted, data about the signal should also be passed.
    callbacks = []

    def register(self, callback):
        """This function appends the target function call to the list of 
        signals stored by this element"""
        signal = {
            'target': callback,
            'condition': True,
        }
        self.callbacks.append(signal)

    def emit(self):
        for signal in self.callbacks:
            if signal['condition']:
                signal['target']()

    def remove(self, target):
        """"""
        try:
            callbacks_list = [cb['target'] for cb in self.callbacks]
            index = callbacks_list.index(target)
            self.callbacks.pop(index)
        except ValueError:
            # want to raise a custom exception here so that it's independent of
            # implementation details in this class.
            raise SignalNotFound(('Signal %s ' % str(target),
                'was not found or was previously removed'))

class UIElement(Communicator):
    attributes = {}
    value = None
    enabled = True
    args_id = None

    def set_value(self, new_value):
# TODO: Is it better python form to raise an exception here instead of
# just not doing anything?
        if not self.is_enabled():
            return

        old_value = self.value
        self.value = new_value
        if old_value != new_value:
            self.emit()

    def get_value(self):
        return self.value

    def _set_enabled(self, enabled):
        self.enabled = enabled
        self.emit()

    def enable(self):
        self._set_enabled(True)

    def disable(self):
        self._set_enabled(False)

    def is_enabled(self):
        return self.enabled


class Group(UIElement):
    elements = []

    def arguments(self):
        output_args = {}
        for element in self.elements:
            try:
                # call the function
                output_args.update(element.arguments())
            except AttributeError:
                # the function did not exist, must have been a primitive
                try:
                    output_args[element.args_id] = element.value()
                except AttributeError:
                    # Args_id does not exist, so we don't care about its output value.
                    pass
        return output_args

class Labeled(object):
    label = u""

    def set_label(self, new_label):
        cast_label = new_label.decode("utf-8")
        self.label = cast_label

    def label(self):
        return self.label

class Text(UIElement, Labeled):
    value = u""

    def set_value(self, new_value):
        # enforce all strings to be utf-8
        cast_value = new_value.decode('utf-8')
        UIElement.set_value(self, cast_value)

class File(Text):
    pass

class OneShotForm(Group):
# Special case group for a one-shot form submission, like what we
# use with a model run.
   pass

# This is the default element type registry, which will be a default
# argument to the UI's registry object.
ELEMENT_REGISTRY = {
    'file': File,
}
