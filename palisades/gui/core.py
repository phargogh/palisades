from palisades.gui import qt4 as toolkit

class Text():
    def __init__(self, core_element):
        self.element = core_element

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
        self._text_field.changed.register(self.element.set_value)
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
