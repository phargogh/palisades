from palisades.gui import qt4 as toolkit

class Application(object):
    def __init__(self):
        object.__init__(self)
        self.app = toolkit.Application()
        self.windows = []

    def add_window(self, form_ptr):
        """Add a window with the appropriate structure of elements.  Assume it's
        a form for now."""
        self.windows.append(Form(form_ptr))

    def execute(self):
        self.app.execute()

class UIObject(object):
    def __init__(self, core_element):
        self.element = core_element

class Group(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)
        self.widget = toolkit.Group()

        # create the elements here.  Elements should probably only ever be
        # created once, not dynamically (though they could be hidden/revealed
        # dynamically), so no need for a separate function.
        for contained_item in core_element.elements:
            # Assume we're only adding a primitive element at the moment.
            # TODO: make sure this works for Groups as well.
            self.widget.add_element(contained_item)

class Text(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)

        label_text = self.element.label()
        self._label = toolkit.Label(label_text)
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

class File(Text):
    def __init__(self, core_element):
        Text.__init__(self, core_element)

        self._file_button = toolkit.FileButton()
        self.widgets = [
            self._validation_button,
            self._label,
            self._text_field,
            self._file_button,
            self._help_button,
        ]

class Form(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)

        self.window = toolkit.FormWindow()
        #TODO: add all the necessary elements here to the form.
        registry = {
            'File': File,
            'Text': Text,
            'Group': Group,
        }

        # loop through all the elements in the form.
        for element in core_element.elements:
            # get the correct element type for the new object using the new
            # element's object's string class name.
            new_element = registry[element.__class__.__name__](element)
            self.add_widget(new_element)

        self.window.submit_pressed.register(self.element.submit)
        #TODO: Add more communicators here ... menu item actions?

    def add_widget(self, new_widget):
       # add the GUI widget here by calling down to the Form's function to do
       # the same.  This is a wrapper function in accordance with the Law of
       # Demeter (see Pragmatic Programmer)
       self.window.add_widget(new_widget)
