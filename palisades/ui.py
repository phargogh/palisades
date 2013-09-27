import os

from PyQt4 import QtGui
from PyQt4 import QtCore

import palisades

LAYOUTS = {
    palisades.LAYOUT_VERTICAL: QtGui.QVBoxLayout,
    palisades.LAYOUT_HORIZONTAL: QtGui.QHBoxLayout,
    palisades.LAYOUT_GRID: QtGui.QGridLayout,
}
ICONS = os.path.join(os.path.dirname(__file__), 'icons')

class Timer(QtCore.QTimer):
    """This is a wrapper class for the QtCore.QTimer class to allow for a python
    threading.Timer instance and functionality."""
    def __init__(self, timeout, callback):
        QtCore.QTimer.__init__(self)
        self.timeout.connect(callback)

    def start(self):
        QtCore.QTimer.start(self)

    def cancel(self):
        self.stop()

class Application():
    app = QtGui.QApplication([''])

class Empty(QtGui.QWidget):
    def __init__(self, configuration={}, layout=None):
        QtGui.QWidget.__init__(self)
        if layout is not None:
            self.set_layout(layout)

    def set_layout(self, layout):
        self.setLayout(LAYOUTS[layout]())

    def add_element(self, element_ptr):
        layout = self.layout()
        if isinstance(layout, QtGui.QGridLayout):
            row = layout.rowCount()
            for column, sub_element in enumerate(element_ptr.elements):
                if sub_element.sizeHint().isValid():
                    sub_element.setMinimumSize(sub_element.sizeHint())
                layout.addWidget(sub_element, row, column)
        else:
            print self.layout()
            print 'not yet implemented'

class Button(QtGui.QPushButton):
    _icon = None
    def __init__(self):
        QtGui.QPushButton.__init__(self)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        if self._icon is not None:
            self.setIcon(QtGui.QIcon(self._icon))

class InformationButton(Button):
    """This class represents the information that a user will see when pressing
        the information button.  This specific class simply represents an object
        that has a couple of string attributes that may be changed at will, and
        then constructed into a cohesive string by calling self.build_contents.

        Note that this class supports the presentation of an error message.  If
        the error message is to be shown to the end user, it must be set after
        the creation of the InformationPopup instance by calling
        self.set_error().
        """
    _icon = os.path.join(ICONS, 'info.png')

    def __init__(self, title, body_text=''):
        """This function initializes the InformationPopup class.
            title - a python string.  The title of the element.
            body_text - a python string.  The body of the text

            returns nothing."""

        Button.__init__(self)
        self.title = title
        self.body_text = body_text
        self.pressed.connect(self.show_info_popup)
        self.setFlat(True)

        # If the user has set "helpText": null in JSON, deactivate.
        if body_text == None:
            self.deactivate()

    def show_info_popup(self):
        """Show the information popup.  This manually (programmatically) enters
            What's This? mode and spawns the tooltip at the location of trigger,
            the element that triggered this function.
            """

        self.setWhatsThis(self.build_contents())  # set popup text
        QtGui.QWhatsThis.enterWhatsThisMode()
        QtGui.QWhatsThis.showText(self.pos(), self.whatsThis(), self)

    def deactivate(self):
        """Visually disable the button: set it to be flat, disable it, and clear
            its icon."""
        self.setFlat(True)
        self.setEnabled(False)
        self.setIcon(QtGui.QIcon(''))

    def set_title(self, title_text):
        """Set the title of the InformationPopup text.  title_text is a python
            string."""
        self.title = title_text

    def set_body(self, body_string):
        """Set the body of the InformationPopup.  body_string is a python
            string."""
        self.body_text = body_string

    def build_contents(self):
        """Take the python string components of this instance of
            InformationPopup, wrap them up in HTML as necessary and return a
            single string containing HTML markup.  Returns a python string."""
        width_table = '<table style="width:400px"></table>'
        title = '<h3 style="color:black">%s</h3><br/>' % (self.title)
        body = '<div style="color:black">%s</div>' % (self.body_text)

        return str(title + body + width_table)

class ValidationButton(InformationButton):
    _error_icon = os.path.join(ICONS, 'validate-fail.png')
    _warning_icon = os.path.join(ICONS, 'dialog-warning.png')
    _pass_icon = os.path.join(ICONS, 'validate-pass.png')
    _STATES = {
        'error': _error_icon,
        'warning': _warning_icon,
        'pass': _pass_icon,
    }

    def __init__(self, title, body_text=''):
        """Initialize the ErrorPopup object.  Adding the self.error_text
        attribute.  Title and body_text are python strings."""
        InformationButton.__init__(self, title, body_text)
        self.error_text = ''
        self.error_state = None
        self.deactivate()

    def setEnabled(self, state):
        if state == False:
            self.setIcon(QtGui.QIcon(''))
        else:
            self.set_error(self.error_text, self.error_state)

        QtGui.QWidget.setEnabled(self, state)

    def set_error(self, error_string, state):
        """Set the error string of this InformationPopup and also set this
            button's icon according to the error contained in error_string.
            error_string is a python string."""

        if state == None:
            state = 'pass'

        self.error_text = error_string
        self.error_state = state
        button_is_flat = False

        try:
            button_icon = self._STATES[state]
        except KeyError:
            button_icon = ''

        if state == 'pass' or state == None:
            button_is_flat = True

        self.setIcon(QtGui.QIcon(button_icon))
        self.setFlat(button_is_flat)
        QtGui.QWidget.setEnabled(self, True)  # enable the button; validation has completed

    def build_contents(self):
        """Take the python string components of this instance of
            InformationPopup, wrap them up in HTML as necessary and return a
            single string containing HTML markup.  Returns a python string."""
        width_table = '<table style="width:400px"></table>'
        title = '<h3 style="color:black">%s</h3><br/>' % (self.title)

        #### CHECK ERROR STATE TO DETERMINE TEXT
        if self.error_state == 'warning':
            color = 'orange'
            text = 'WARNING:'
        elif self.error_state == 'error':
            color = 'red'
            text = 'ERROR:'
        else:
            color = 'green'
            text = 'Validation successful'

        message = '<b style="color:%s">%s %s</b><br/>' % (color, text,
            self.error_text)

        body = '<div style="color:black">%s</div>' % (self.body_text)

        return str(title + message + body + width_table)

class Label(QtGui.QLabel):
    pass

class TextField(QtGui.QLineEdit):
    pass

class FileButton(Button):
    _icon = os.path.join(ICONS, 'document-open.png')


class Text():
    elements = []

    def __init__(self, configuration):
        label_text = configuration['label']
        self._label = Label(label_text)
        self._validation_button = ValidationButton(label_text)
        self._text_field = TextField()
        self._help_button = InformationButton(label_text)

        self._text_field.setMaximumWidth(configuration['width'])

        self.elements = [
            self._validation_button,
            self._label,
            self._text_field,
            Empty(),
            self._help_button
        ]

    def set_value(self, value):
        self._text_field.setText(value)

    def set_label(self, value):
        self._label.setText(value)

    def set_callback(self, callback):
        self._text_field.textChanged.connect(callback)

    def value(self):
        return unicode(self._text_field.text(), 'utf-8')

    def set_error(self, error, state):
        # set the error message in the Qt-style validation button.
        self._validation_button.set_error(error, state)
        if self._validation_button.error_state == 'error':
            self._label.setStyleSheet('color: red')
            self._text_field.setStyleSheet('border: 1px solid red')
        else:
            self._label.setStyleSheet('')
            self._text_field.setStyleSheet('')

class File(Text):

    def __init__(self, configuration):
        Text.__init__(self, configuration)
        self._file_button = FileButton()

        self.elements = [
            self._validation_button,
            self._label,
            self._text_field,
            self._file_button,
            self._help_button
        ]



