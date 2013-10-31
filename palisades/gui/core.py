from palisades.gui import qt4 as toolkit

from palisades.validation import V_ERROR

import pdb

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

class GroupGUI(UIObject):
    def __init__(self, core_element, registrar):
        UIObject.__init__(self, core_element)

        self.registrar = registrar
        self.widgets = toolkit.Group(core_element.label())
        self.elements = []

        # create the elements here.  Elements should probably only ever be
        # created once, not dynamically (though they could be hidden/revealed
        # dynamically), so no need for a separate function.
#        for element in core_element.elements:
#            # Assume we're only adding a primitive element at the moment.
#            # TODO: make sure this works for Groups as well.
#            self.widget.add_element(element)
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

class ContainerGUI(GroupGUI):
    pass

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

class FormGUI(UIObject):
    def __init__(self, core_element):
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

        self.group = GroupGUI(self.element._ui, registry)
        self.window = toolkit.FormWindow(self.group.widgets)
        self.quit_confirm = toolkit.ConfirmQuitDialog()

#        # loop through all the elements in the form.
#        for element in core_element.elements:
#            print element
#            # get the correct element type for the new object using the new
#            # element's object's string class name.
#            # TODO: if element is a Group, it must create its contained widgets
#            try:
#                element_classname = element.__class__.__name__
#                new_element = registry[element_classname](element)
#            except TypeError:
#                # Happens when the element's GUI representation in registry is
#                # None, meaning that there should not be a GUI display.
#                new_element = None
#
#            # If the new element is None, there's no visualization.  Skip.
#            if new_element is not None:
#                if isinstance(new_element, GroupGUI):
#                    self.window.add_widget(new_element, self.registrar)
#                else:
#                    self.window.add_widget(new_element)

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

#    def add_widget(self, new_widget):
#       # add the GUI widget here by calling down to the Form's function to do
#       # the same.  This is a wrapper function in accordance with the Law of
#       # Demeter (see Pragmatic Programmer)
#       self.window.add_widget(new_widget)
