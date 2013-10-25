import os
import threading

from PyQt4 import QtGui
from PyQt4 import QtCore

#from PySide import QtGui
#from PySide import QtCore

import palisades
from palisades.gui import ICON_BULB_BIG
from palisades.gui import ICON_CHECKMARK
from palisades.gui import ICON_CLOSE
from palisades.gui import ICON_ENTER
from palisades.gui import ICON_ERROR
from palisades.gui import ICON_ERROR_BIG
from palisades.gui import ICON_FOLDER
from palisades.gui import ICON_INFO
from palisades.gui import ICON_REFRESH
from palisades.gui import ICON_UNDO
from palisades.gui import ICON_WARN
from palisades.gui import ICON_WARN_BIG
from palisades.utils import Communicator

LAYOUTS = {
    palisades.LAYOUT_VERTICAL: QtGui.QVBoxLayout,
    palisades.LAYOUT_HORIZONTAL: QtGui.QHBoxLayout,
    palisades.LAYOUT_GRID: QtGui.QGridLayout,
}
ICONS = os.path.join(os.path.dirname(__file__), 'icons')

def center_window(window_ptr):
    """Center a window on whatever screen it appears.

            window_ptr - a pointer to a Qt window, whether an application or a
                QDialog.

        returns nothing."""
    geometry = window_ptr.frameGeometry()
    center = QtGui.QDesktopWidget().availableGeometry().center()
    geometry.moveCenter(center)
    window_ptr.move(geometry.topLeft())

class Application(object):
    def __init__(self, args=None):
        app = QtGui.QApplication.instance()
        if app is None:
            app = QtGui.QApplication([''])
        self.app = app

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
#        if layout is not None:
#            self.set_layout(layout)

#    def set_layout(self, layout):
#        self.setLayout(LAYOUTS[layout]())

#    def add_element(self, element_ptr, row_index=None):
#        layout = self.layout()
#        if isinstance(layout, QtGui.QGridLayout):
#            if row_index is None:
#                row = layout.rowCount()
#            else:
#                row = row_index
#            for column, sub_element in enumerate(element_ptr.elements):
#                if sub_element.sizeHint().isValid():
#                    sub_element.setMinimumSize(sub_element.sizeHint())
#                layout.addWidget(sub_element, row, column)
#        else:
#            print self.layout()
#            print 'not yet implemented'

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
    _icon = ICON_INFO

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

        self._disabled_icon = QtGui.QIcon('')

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
        self.setIcon(self._disabled_icon)

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
    _error_icon = ICON_ERROR
    _warning_icon = ICON_WARN
    _pass_icon = ICON_CHECKMARK
    _STATES = {
        'error': QtGui.QIcon(_error_icon),
        'warning': QtGui.QIcon(_warning_icon),
        'pass': QtGui.QIcon(_pass_icon),
        None: QtGui.QIcon(''),
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
            self.setIcon(self._STATES[None])
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
            button_icon = self._STATES[None]

        if state == 'pass' or state == None:
            button_is_flat = True

        self.setIcon(button_icon)
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
    #error_changed = QtCore.Signal(bool)
    error_changed = QtCore.pyqtSignal(bool)

    def __init__(self, label_text):
        QtGui.QLabel.__init__(self, label_text)
        self.error_changed.connect(self._set_error)

    def set_error(self, is_error):
        """Change the styling of this label according to is_error.

            is_error - True if there is an error with the associated input, False if not.

        Returns nothing."""

        # For some reason, usin this sometimes prints an error message saying 
        # "QPixmap: It is not safe to use pixmaps outside the GUI thread"
        # I'm leaving it alone for now, since the application seems to work ok
        # without it.
        self.error_changed.emit(is_error)


    def _set_error(self, is_error):
        print 'Label - current thread: %s' % threading.current_thread()
        if is_error:
            self.setStyleSheet("QWidget { color: red }")
        else:
            self.setStyleSheet("QWidget {}")

class TextField(QtGui.QLineEdit):
    #error_changed = QtCore.Signal(bool)
    error_changed = QtCore.pyqtSignal(bool)

    def __init__(self, starting_value):
        QtGui.QLineEdit.__init__(self, starting_value)
        self.setMinimumWidth(400)

        # set up my communicator instances and connect them to the correct Qt
        # signals.
        self.value_changed = Communicator()
        self.textChanged.connect(self._value_changed)
        self.error_changed.connect(self._set_error)

    def _value_changed(self, qstring_value):
        """Callback for the TextChanged signal.  Casts to a python string anc
        emits the value_changed communicator signal."""
        qstring_value = self.text()
        new_value = unicode(qstring_value, 'utf-8')
        self.value_changed.emit(new_value)

    def set_error(self, is_error):
        """Change the styling of this textfield according to is_error.

            is_error - True if there is an error with the input, False if not.

        Returns nothing."""
        self.error_changed.emit(is_error)

    def _set_error(self, is_error):
        print 'Textfield - current thread: %s' % threading.current_thread()
        if is_error:
            self.setStyleSheet("QWidget { border: 1px solid red }")
        else:
            self.setStyleSheet("QWidget {}")

    def set_text(self, new_value):
        self.setText(new_value)

    def contextMenuEvent(self, event=None):
        """Reimplemented from QtGui.QLineEdit.contextMenuEvent.

        This function allows me to make changes to the context menu when one
        is requested before I show the menu."""
        menu = self.createStandardContextMenu()
        refresh_action = QtGui.QAction('Refresh', menu)
        refresh_action.setIcon(QtGui.QIcon(ICON_REFRESH))
        refresh_action.triggered.connect(self._value_changed)
        menu.addAction(refresh_action)
        menu.exec_(event.globalPos())


class FileButton(Button):
    _icon = ICON_FOLDER

    def __init__(self):
        Button.__init__(self)
        self.file_dialog = FileDialog()
        self.clicked.connect(self._get_file)

        self.file_selected = Communicator()

    def _get_file(self):
        filename = self.file_dialog.get_file('file')
        self.file_selected.emit(filename)

class FileDialog(QtGui.QFileDialog):
    filters = {
        "all": ["All files (* *.*)"],
        "EXISTS": ["All files (* *.*)"],
        "CSV": ["Comma separated value file (*.csv *.CSV)"],
        "GDAL": ["[GDAL] Arc/Info Binary Grid (hdr.adf HDR.ADF hdr.ADF)",
                 "[GDAL] Arc/Info ASCII Grid (*.asc *.ASC)",
                 "[GDAL] GeoTiff (*.tif *.tiff *.TIF *.TIFF)"],
        "OGR": ["[OGR] ESRI Shapefiles (*.shp *.SHP)"],
        "DBF": ["[DBF] dBase legacy file (*dbf *.DBF)"],
    }

    def __init__(self):
        QtGui.QFileDialog.__init__(self)
        self.last_filter = QtCore.QString()

    def get_file(self, title, default_folder='~'):
        default_folder = os.path.expanduser(default_folder)
        dialog_title = 'Select ' + title

        filename, filter = self.getOpenFileNameAndFilter(
            self, dialog_title, default_folder, initialFilter=self.last_filter)
        self.last_filter = filter

        return unicode(filename, 'utf-8')

class InfoDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.messages = []
        self.resize(400, 200)
        self.setWindowTitle('Errors exist!')
        self.setLayout(QtGui.QVBoxLayout())
        self.icon = QtGui.QLabel()
        self.icon.setStyleSheet('QLabel { padding: 10px }')
        self.set_icon(ICON_ERROR_BIG)
        self.icon.setSizePolicy(QtGui.QSizePolicy.Fixed,
            QtGui.QSizePolicy.Fixed)
        self.title = QtGui.QLabel()
        self.set_title('Whoops!')
        self.title.setStyleSheet('QLabel { font: bold 18px }')
        self.body = QtGui.QLabel()
        self.body.setWordWrap(True)
        self.ok_button = QtGui.QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)

        error_widget = QtGui.QWidget()
        error_widget.setLayout(QtGui.QHBoxLayout())
        error_widget.layout().addWidget(self.icon)
        self.layout().addWidget(error_widget)

        body_widget = QtGui.QWidget()
        error_widget.layout().addWidget(body_widget)
        body_widget.setLayout(QtGui.QVBoxLayout())
        body_widget.layout().addWidget(self.title)
        body_widget.layout().addWidget(self.body)

        self.button_box = QtGui.QDialogButtonBox()
        self.button_box.addButton(self.ok_button, QtGui.QDialogButtonBox.AcceptRole)
        self.layout().addWidget(self.button_box)

    def showEvent(self, event=None):
        center_window(self)
        print 'showing dialog!'
        QtGui.QDialog.showEvent(self, event)

    def set_icon(self, uri):
        self.icon.setPixmap(QtGui.QPixmap(uri))

    def set_title(self, title):
        self.title.setText(title)

    def set_messages(self, message_list):
        self.messages = message_list

    def confirm(self):
        exit_code = self.exec_()
        if exit_code != 0:
            return True
        return False

class WarningDialog(InfoDialog):
    def __init__(self):
        InfoDialog.__init__(self)
        self.set_title('Warning...')
        self.set_icon(ICON_WARN_BIG)
        self.body.setText('Some inputs cannot be validated and may cause ' +
           'this program to fail.  Continue anyways?')
        self.no_button = QtGui.QPushButton('Back')
        self.no_button.clicked.connect(self.reject)
        self.button_box.addButton(self.no_button, QtGui.QDialogButtonBox.RejectRole)

class ConfirmQuitDialog(WarningDialog):
    def __init__(self):
        WarningDialog.__init__(self)
        self.setWindowTitle('Are you sure you want to quit?')
        self.set_title('Really quit?')
        self.set_icon(ICON_BULB_BIG)
        self.body.setText('You will lose any changes to your parameter fields.')
        self.ok_button.setText('Quit')

class ErrorDialog(InfoDialog):
    def __init__(self):
        InfoDialog.__init__(self)
        self.set_title('Whoops!')

    def showEvent(self, event=None):
        label_string = '<ul>'
        for element_tuple in self.messages:
            label_string += '<li>%s: %s</li>' % element_tuple
        label_string += '</ul>'

        num_messages = len(self.messages)
        if num_messages == 1:
            num_error_string = 'is 1 error'
        else:
            num_error_string = 'are %s errors' % num_messages

        self.body.setText(str("There %s that must be resolved" +
            " before this tool can be run:%s") % (num_error_string, label_string))
        self.body.setMinimumSize(self.body.sizeHint())
        InfoDialog.showEvent(self)

# TODO: make this a QWidget, and a widget inside this widget's layout be the
# form with all its element.  This will mean creating wrapper functions for most
# of the calls to the UI embedded herein.
class FormWindow(QtGui.QWidget):
    """A Form is a window where you have a set of inputs that the user fills in
    or configures and then presses 'submit'."""
    def __init__(self):
        QtGui.QWidget.__init__(self)

        # The form has two elements arranged vertically: the form window (which
        # may eventually need to be scrollable) and the buttonbox.
        self.setLayout(QtGui.QVBoxLayout())
        print 'Form layout: %s' % self.layout()

        # create communicators.
        self.submit_pressed = Communicator()
        self.quit_requested = Communicator()

        # Create the QWidget pane for the inputs and add it to the layout.
        self.input_pane = QtGui.QWidget()
        self.input_pane.setLayout(QtGui.QGridLayout())
        self.layout().addWidget(self.input_pane)

        # Create the buttonBox and add it to the layout.
        self.run_button = QtGui.QPushButton(' Run')
        self.run_button.setIcon(QtGui.QIcon(os.path.join(ICON_ENTER)))

        self.quit_button = QtGui.QPushButton(' Quit')
        self.quit_button.setIcon(QtGui.QIcon(os.path.join(ICON_CLOSE)))

        self.reset_button = QtGui.QPushButton(' Reset')
        self.reset_button.setIcon(QtGui.QIcon(os.path.join(ICON_UNDO)))

        #create the buttonBox (a container for buttons)
        self.button_box = QtGui.QDialogButtonBox()
        self.button_box.addButton(self.run_button, QtGui.QDialogButtonBox.AcceptRole)
        self.button_box.addButton(self.quit_button, QtGui.QDialogButtonBox.RejectRole)
        self.button_box.addButton(self.reset_button, QtGui.QDialogButtonBox.ResetRole)

        #connect the buttons to their functions.
#        self.run_button.clicked.connect(self.okPressed)
        self.quit_button.clicked.connect(self._quit_pressed)
#        self.reset_button.clicked.connect(self.resetParametersToDefaults)

        #add the buttonBox to the window.
        self.layout().addWidget(self.button_box)
        self.close_confirmed = False

    def showEvent(self, event):
        center_window(self)
        QtGui.QWidget.showEvent(self, event)

    def _quit_pressed(self):
        print 'quit pressed, emitting'
        if not self.close_confirmed:
            self.quit_requested.emit(True)


    def close(self):
        # If close() is called, we know for sure that we want to close thw
        # window, no questions asked.
        self.close_confirmed = True
        QtGui.QWidget.close(self)

    def closeEvent(self, event=None):
        print 'closing!'
        print 'actually, simulating a Quit press'
        self._quit_pressed()

    def add_widget(self, gui_object):
        # do the logic of adding the widgets of the gui_object to the Qt Widget.
        layout = self.input_pane.layout()
        current_row = layout.rowCount()

        print 'Form - current thread: %s' % threading.current_thread()
        print 'adding gui_object %s' % gui_object
        if isinstance(gui_object, palisades.gui.core.TextGUI):
            print 'item is TextGUI or subclass'
            for col_index, qt_widget in enumerate(gui_object.widgets):
                if qt_widget is None:
                    qt_widget = Empty()
                qt_widget.setVisible(True)
                print (qt_widget, current_row, col_index, qt_widget.isVisible())
                self.input_pane.layout().addWidget(qt_widget, current_row, col_index)
                qt_widget.show()
        else:
            num_cols = layout.columnCount()
            print 'item is group'
            self.input_pane.layout().addWidget(gui_object.widget, current_row, 0, 1, num_cols)
            gui_object.widget.show()
