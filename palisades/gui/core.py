from types import *

from palisades.gui import qt4 as toolkit
from palisades.validation import V_ERROR

class NotYetImplemented(Exception): pass

class ApplicationGUI(object):
    def __init__(self):
        object.__init__(self)
        self.app = toolkit.Application()
        self.windows = []
        self.window = None

    def add_window(self, form_ptr):
        """Add a window with the appropriate structure of elements.  Assume it's
        a form for now."""
        self.window = FormGUI(form_ptr)
        self.windows.append(self.window)

    def execute(self):
        for window in self.windows:
            print window
            window.show()
        self.app.execute()

class UIObject(object):
    def __init__(self, core_element):
        self.element = core_element

        self.element.visibility_changed.register(self.set_visibility)

    def set_visibility(self, is_visible):
        """Update the element's visibility in the toolkit."""
        raise NotYetImplemented

class GroupGUI(UIObject):
    def __init__(self, core_element, registrar=None):
        UIObject.__init__(self, core_element)

        #TODO: add all the necessary elements here to the form.
        registry = {
            'File': FileGUI,
            'Text': TextGUI,
            'Group': GroupGUI,
            'Label': LabelGUI,
            'Static': None,  # None means no GUI display.
            'Dropdown': DropdownGUI,
            'Container': ContainerGUI,
        }

        if registrar != None:
            assert type(registrar) is DictType
            registry.update(registrar)

        self.registrar = registry

        # If a subclass has already set up a toolkit widget for this object, we
        # want to use that widget.  Assumes that the widget is a subclass of
        # toolkit.Group.
        if not hasattr(self, 'widgets'):
            self.widgets = toolkit.Group()

        self.elements = []

        # create the elements here.  Elements should probably only ever be
        # created once, not dynamically (though they could be hidden/revealed
        # dynamically), so no need for a separate function.
        for element in core_element._elements:
            print 'GROUP', element
            # get the correct element type for the new object using the new
            # element's object's string class name.
            # TODO: if element is a Group, it must create its contained widgets
            try:
                element_classname = element.__class__.__name__
                cls = self.registrar[element_classname]
                if element_classname in ['Group', 'Container']:
                    print 'MAKING NEW GROUP: %s' % element_classname
                    new_element = cls(element, self.registrar)
                else:
                    new_element = cls(element)
            except TypeError as error:
                # Happens when the element's GUI representation in registry is
                # None, meaning that there should not be a GUI display.
                new_element = None
                print 'ERROR ERROR: %s in %s' % (error, element_classname)

            # If the new element is None, there's no visualization.  Skip.
            if new_element is not None:
                self.widgets.add_widget(new_element)
                self.elements.append(new_element)

    def set_visibility(self, is_visible):
        """Set the visibility of this element."""
        self.widgets.set_visible(is_visible)

class ContainerGUI(GroupGUI):
    def __init__(self, core_element, registrar=None):
        self.widgets = toolkit.Container(core_element.label())
        GroupGUI.__init__(self, core_element, registrar)
        self.widgets.set_collapsible(self.element.is_collapsible())

        # when the container is collapsed by the GUI user, set the underlying
        # element to be collapsed
        self.widgets.checkbox_toggled.register(self.element.set_collapsed)

class TextGUI(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)

        label_text = self.element.label()
        self._label = toolkit.ElementLabel(label_text)
        self._validation_button = toolkit.ValidationButton(label_text)
        self._text_field = toolkit.TextField(self.element.value())
        self._help_button = toolkit.InformationButton(label_text)

        self.widgets = [
            self._validation_button,
            self._label,
            self._text_field,
            None,
            self._help_button,
        ]

        # when the text is modified in the textfield, call down to the element
        # to set the text
        self._text_field.value_changed.register(self.element.set_value)
        # I'm deliberately deciding to not care about when the core's value is
        # changed programmatically while a UI is active.

        self.element.validation_completed.register(self._update_validation)

    def _update_validation(self, error_state):
        # error_state is a tuple of (error_state, error_msg)
        error_msg, error = error_state
        self._validation_button.set_error(error_msg, error)
        self._text_field.set_error(error == V_ERROR)
        self._label.set_error(error == V_ERROR)

class FileGUI(TextGUI):
    def __init__(self, core_element):
        TextGUI.__init__(self, core_element)

        self._file_button = toolkit.FileButton()
        self._file_button.file_selected.register(self._file_selected)

        self.widgets = [
            self._validation_button,
            self._label,
            self._text_field,
            self._file_button,
            self._help_button,
        ]

    def _file_selected(self, new_value):
        # set the textfield's value
        self._text_field.set_text(new_value)

        # set the core element's value
        self.element.set_value(new_value)

class DropdownGUI(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)

        label_text = self.element.label()
        self._label = toolkit.ElementLabel(label_text)
        self._dropdown = toolkit.Dropdown(self.element.options,
            self.element.current_index())
        self._help_button = toolkit.InformationButton(label_text)

        self.widgets = [
            None,
            self._label,
            self._dropdown,
            None,
            self._help_button
        ]

        self._dropdown.value_changed.register(self.element.set_value)

class LabelGUI(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)
        self.widgets = toolkit.Label(self.element.label())

class FormGUI():
    def __init__(self, core_element):
        self.element = core_element

        self.group = GroupGUI(self.element._ui)
        self.window = toolkit.FormWindow(self.group.widgets)
        self.quit_confirm = toolkit.ConfirmQuitDialog()

        self.window.submit_pressed.register(self.element.submit)
        self.window.quit_requested.register(self.close)
        #TODO: Add more communicators here ... menu item actions?

    def show(self):
        self.window.show()

    def close(self, data=None):
        print 'user requested quit'
        print 'showing dialog'
        if self.quit_confirm.confirm():
            self.window.close()

