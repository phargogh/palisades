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

class Application(object):
    def __init__(self):
        object.__init__(self)
        self.app = QtGui.QApplication([''])

    def execute(self):
        self.app.exec_()

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

class Empty(QtGui.QWidget):
    def __init__(self, configuration={}, layout=None):
        QtGui.QWidget.__init__(self)
        if layout is not None:
            self.set_layout(layout)

    def set_layout(self, layout):
        self.setLayout(LAYOUTS[layout]())

    def add_element(self, element_ptr, row_index=None):
        layout = self.layout()
        if isinstance(layout, QtGui.QGridLayout):
            if row_index is None:
                row = layout.rowCount()
            else:
                row = row_index
            for column, sub_element in enumerate(element_ptr.elements):
                if sub_element.sizeHint().isValid():
                    sub_element.setMinimumSize(sub_element.sizeHint())
                layout.addWidget(sub_element, row, column)
        else:
            print self.layout()
            print 'not yet implemented'

# currently just a wrapper for the Empty class that has a more appropriate name.
class Group(Empty):
    pass

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
    def __init__(self, starting_value):
        QtGui.QLineEdit.__init__(self, starting_value)

        # set up my communicator instances and connect them to the correct Qt
        # signals.
        self.value_changed = palisades.core.Communicator()
        self.textChanged.connect(self._value_changed)

    def _value_changed(self, qstring_value):
        """Callback for the TextChanged signal.  Casts to a python string anc
        emits the value_changed communicator signal."""
        new_value = unicode(qstring_value, 'utf-8')
        self.value_changed.emit(new_value)

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

# TODO: make this a QWidget, and a widget inside this widget's layout be the
# form with all its element.  This will mean creating wrapper functions for most
# of the calls to the UI embedded herein.
class FormWindow(Empty):
    """A Form is a window where you have a set of inputs that the user fills in
    or configures and then presses 'submit'."""
    def __init__(self, configuration={}, layout=None):
        Empty.__init__(self, configuration, layout)

        # The form has two elements arranged vertically: the form window (which
        # may eventually need to be scrollable) and the buttonbox.
        self.setLayout(QtGui.QVBoxLayout())

        # create communicators.
        self.submit_pressed = palisades.core.Communicator()

        # Create the QWidget pane for the inputs and add it to the layout.
        self.input_pane = QtGui.QWidget()
        self.input_pane.setLayout(QtGui.QGridLayout())
        self.layout().addWidget(self.input_pane)

        # Create the buttonBox and add it to the layout.
        self.run_button = QtGui.QPushButton(' Run')
        self.run_button.setIcon(QtGui.QIcon(os.path.join(ICONS,
            'dialog-ok.png')))

        self.cancel_button = QtGui.QPushButton(' Quit')
        self.cancel_button.setIcon(QtGui.QIcon(os.path.join(ICONS,
            'dialog-close.png')))

        self.reset_button = QtGui.QPushButton(' Reset')
        self.reset_button.setIcon(QtGui.QIcon(os.path.join(ICONS,
            'edit-undo.png')))

        #create the buttonBox (a container for buttons)
        self.button_box = QtGui.QDialogButtonBox()
        self.button_box.addButton(self.run_button, QtGui.QDialogButtonBox.AcceptRole)
        self.button_box.addButton(self.cancel_button, QtGui.QDialogButtonBox.RejectRole)
        self.button_box.addButton(self.reset_button, QtGui.QDialogButtonBox.ResetRole)

        #connect the buttons to their functions.
#        self.run_button.clicked.connect(self.okPressed)
#        self.cancel_button.clicked.connect(self.closeWindow)
#        self.reset_button.clicked.connect(self.resetParametersToDefaults)

        #add the buttonBox to the window.
        self.layout().addWidget(self.button_box)

    def add_widget(self, toolkit_widget):
        # do the logic of adding the widget to the Qt Widget.
        for widget in toolkit_widget.widgets:
            # if we're dealing with a primitive, just add all the elements to
            # the grid.
            # right now, all primitives are subclasses of the Text class.
            layout = self.input_pane.layout()
            current_row = layout.rowCount()
            if isinstance(widget, Text):
                print 'adding widget %s' % widget
                for col_index, qt_widget in enumerate(widget.elements):
                    layout.addWidget(qt_widget, current_row, col_index)
            else:
                # if we're dealing with a group which will eventually contain
                # elements
                print 'adding non-primitive %s from %s' % (widget,
                        toolkit_widget)
                num_cols = layout.columnCount()
                layout.addWidget(widget, current_row, 0, 1, num_cols)
