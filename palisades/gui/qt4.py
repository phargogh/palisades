import os
import traceback
import threading
from types import BooleanType

from PyQt4 import QtGui
from PyQt4 import QtCore
Signal = QtCore.pyqtSignal

#from PySide import QtGui
#from PySide import QtCore
#Signal = QtCore.Signal
#QtCore.QString = unicode  # pySide uses unicode objects for qstring

import palisades
import palisades.gui
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
from palisades.gui import ICON_MINUS
from palisades.utils import Communicator
import palisades.i18n

_ = palisades.i18n.language.ugettext
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

        lang = palisades.i18n.language.current_lang
        self.translator = QtCore.QTranslator()
        self.translator.load("qt_%s" % lang,
            QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
        self.app.installTranslator(self.translator)

    def execute(self):
        self.app.exec_()

#class QtWidget(QtGui.QWidget):
class QtWidget(object):
    # REQUIRED: subclasses must also be a subclass of QWidget
    def set_visible(self, is_visible):
        self.setVisible(is_visible)

    def is_visible(self):
        return self.isVisible()

class Empty(QtGui.QWidget, QtWidget):
    pass

class Group(QtGui.QGroupBox, QtWidget):
    def __init__(self):
        QtGui.QGroupBox.__init__(self)
        QtWidget.__init__(self)
        self.setLayout(QtGui.QGridLayout())

    def add_widget(self, gui_object, start_index=0):
        # do the logic of adding the widgets of the gui_object to the Qt Widget.
        layout = self.layout()
        current_row = layout.rowCount()

        # If the item has a widgets attribute that is a list, we assume that we
        # want to add widgets to the UI in that order.
        if isinstance(gui_object.widgets, list):
            for col_index, qt_widget in enumerate(gui_object.widgets, start_index):
                if qt_widget is None:
                    qt_widget = Empty()
                qt_widget.setMinimumSize(qt_widget.sizeHint())
                self.layout().addWidget(qt_widget, current_row, col_index)
        # If the item's widgets attribute is not a list (it's assumed to be a
        # toolkit widget), then we want to add that widget to span the whole of
        # a single row.
        else:
            # need this just in case a label object is the first in a Group.  If
            # it is, then there would not be any columns, which throws off the
            # rest of the layout.
            num_cols = max(5 + start_index, layout.columnCount())
            gui_object.widgets.setMinimumSize(gui_object.widgets.sizeHint())
            self.layout().addWidget(gui_object.widgets, current_row, 0 +
                    start_index, 1, num_cols)
        self.layout().setRowStretch(current_row, 0)

class Container(Group):
    def __init__(self, label_text):
        Group.__init__(self)
        self.setTitle(label_text)

        self.checkbox_toggled = Communicator()
        self.toggled.connect(self._container_toggled)

    def _container_toggled(self):
        # returns whether the container is collapsed.
        self.checkbox_toggled.emit(self.is_collapsed())
        self.setMinimumSize(self.sizeHint())
        self.update()

    def set_collapsible(self, is_collapsible):
        self.setCheckable(is_collapsible)

    def is_collapsible(self):
        return self.isCheckable()

    def is_collapsed(self):
        # When a collapsible container is checked, it's expanded.
        # When a collapsible container is unchecked, it's collapsed.
        # Therefore, return the opposite of the check state.
        return not self.isChecked()

    def set_collapsed(self, is_collapsed):
        # TODO: add a toolkit test for this function.
        if self.is_collapsible():
            self.setChecked(not is_collapsed)
        else:
            raise RuntimeError('Cannot collapse a container that is not '
                'collapsible')

class Button(QtGui.QPushButton, QtWidget):
    _icon = None
    def __init__(self):
        QtWidget.__init__(self)
        QtGui.QPushButton.__init__(self)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        if self._icon is not None:
            self.setIcon(QtGui.QIcon(self._icon))

    def set_active(self, is_active):
        """Activate or deactivate the button.  If is_active is True, the button
        will be enabled.  False if not."""

        assert type(is_active) is BooleanType, 'is_active must be True or False'
        self.setEnabled(is_active)

class Multi(Container):
    class MinusButton(Button):
        def __init__(self, row_index):
            Button.__init__(self)
            self._row_index = row_index
            self.pushed = Communicator()
            self.released.connect(self._button_pushed)
            self.setIcon(QtGui.QIcon(ICON_MINUS))
            self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        def _button_pushed(self):
            self.pushed.emit(self._row_index)

    class AddElementLink(QtGui.QLabel):
        def __init__(self, link_text):
            template = '<a href="naturalcapitalproject.org">%s</a>'
            rendered_link = template % link_text
            QtGui.QLabel.__init__(self, rendered_link)

            self.clicked = Communicator()
            self.linkActivated.connect(self.clicked.emit)

    def __init__(self, label_text, link_text):
        Container.__init__(self, label_text)

        # TODO: implement defaultValue

        self.element_requested = Communicator()
        self.element_added = Communicator()
        self.element_removed = Communicator()

        self.add_element_link = self.AddElementLink(link_text)
        self.add_element_link.clicked.register(self.element_requested.emit)
        self.layout().addWidget(self.add_element_link,
            self.layout().rowCount(), 2)

        self.setMinimumSize(self.sizeHint())
        self.update()
        self._active_elements = []

    def count(self):
        # return the number of elements in the layout that are active.
        return len(self._active_elements)

    def _remove_element(self, layout_row_num):
        # get the internal row number based on the row_num passed in
        element_index = self._active_elements.index(layout_row_num)
        element_ordinal = self._active_elements.pop(element_index)

        # instead of actually removing the widgets (likely to cause segfault
        # problems while testing), I'll just hide the widgets.  They're
        # invisible to the user when this happens, and the core element is the
        # one that actually reports element values.
        for j in range(self.layout().columnCount()):
            sub_item = self.layout().itemAtPosition(layout_row_num, j)
            if sub_item != None:  # None when no widget is there.
                sub_widget = sub_item.widget()
                sub_widget.hide()

        self.layout().setRowMinimumHeight(layout_row_num, 0)
        self.setMinimumSize(self.sizeHint())
        self.update()
        self.element_removed.emit(element_index)

    def add_widget(self, gui_object=None):
        # when an element is added, it must universally have a minus button in
        # front of it.  This should apply to when the element is supposed to
        # span all columns as well as when there are a number of individual
        # widgets.
        #minus_button = self.MinusButton(self.count())
        row_number = self.layout().rowCount()
        minus_button = self.MinusButton(row_number)
        minus_button.pushed.register(self._remove_element)
        if isinstance(gui_object.widgets, list):
            gui_object.widgets.insert(0, minus_button)
            Container.add_widget(self, gui_object)

        # keep track of the row that we're adding so we can more easily access
        # the widget later on
        self._active_elements.append(row_number)

        # readjust the minimum size to accommodate the new elements.
        self.setMinimumSize(self.sizeHint())
        self.update()

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
        self._title = title
        self._body_text = body_text
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

    def set_title(self, title_text):
        """Set the title of the InformationPopup text.  title_text is a python
            string."""
        self._title = title_text

    def title(self):
        """Return the title of the button"""
        return self._title

    def set_body(self, body_string):
        """Set the body of the InformationPopup.  body_string is a python
            string."""
        self._body_text = body_string

    def body(self):
        """Return the string body of the InformationPopup."""
        return self._body_text

    def build_contents(self):
        """Take the python string components of this instance of
            InformationPopup, wrap them up in HTML as necessary and return a
            single string containing HTML markup.  Returns a python string."""
        width_table = '<table style="width:400px"></table>'
        title = '<h3 style="color:black">%s</h3><br/>' % (self.title())
        body = '<div style="color:black">%s</div>' % (self.body())

        return str(title + body + width_table)

class ValidationButton(InformationButton):
    _error_icon = ICON_ERROR
    _warning_icon = ICON_WARN
    _pass_icon = ICON_CHECKMARK

    def __init__(self, title, body_text=''):
        """Initialize the ErrorPopup object.  Adding the self.error_text
        attribute.  Title and body_text are python strings."""
        self._states = {
            'error': QtGui.QIcon(self._error_icon),
            'warning': QtGui.QIcon(self._warning_icon),
            'pass': QtGui.QIcon(self._pass_icon),
            None: QtGui.QIcon(''),
        }
        InformationButton.__init__(self, title, body_text)
        self.error_text = ''
        self.error_state = 'pass'

        self.set_active(False)

    def has_error(self):
        # return whether there is an error or validation warning.
        if self.error_state == 'pass':
            return False
        return True

    def set_active(self, is_active):
        """Set the active state of the button based on the error state of the
        button.

        is_active - a boolean.  If True, the button will be enabled.  If
            False, the button will be disabled.

        Reimplemented from InformationButton.set_active."""
        InformationButton.set_active(self, is_active)

        if is_active is False:
            self.setIcon(self._states[None])
            self.setFlat(True)
        else:
            self.setIcon(self._states[self.error_state])
            if self.error_state == 'pass':
                self.setFlat(True)
            else:
                self.setFlat(False)

    def set_error(self, error_string, state):
        """Set the error string of this InformationPopup and also set this
            button's icon according to the error contained in error_string.
            error_string is a python string."""

        assert state in ['pass', 'warning', 'error'], ('Error state must be '
            'one of "pass", "warning" or "error", %s found"' % state)

        self.error_text = error_string
        self.error_state = state
        self.set_active(True)

    def build_contents(self):
        """Take the python string components of this instance of
            InformationPopup, wrap them up in HTML as necessary and return a
            single string containing HTML markup.  Returns a python string."""
        width_table = '<table style="width:400px"></table>'
        title = '<h3 style="color:black">%s</h3><br/>' % (self.title())

        #### CHECK ERROR STATE TO DETERMINE TEXT
        if self.error_state == 'warning':
            color = 'orange'
            text = _('WARNING:')
        elif self.error_state == 'error':
            color = 'red'
            text = _('ERROR:')
        else:
            color = 'green'
            text = _('Validation successful')

        message = '<b style="color:%s">%s %s</b><br/>' % (color, text,
            self.error_text)

        body = '<div style="color:black">%s</div>' % (self.body())

        return str(title + message + body + width_table)

class Label(QtGui.QLabel, QtWidget):
    def __init__(self, label_text):
        QtWidget.__init__(self)
        QtGui.QLabel.__init__(self, label_text)
        self.setTextFormat(QtCore.Qt.RichText)
        self.setWordWrap(True)

    def is_visible(self):
        return self.isVisible()

class ElementLabel(QtGui.QLabel, QtWidget):
    error_changed = Signal(bool)

    def __init__(self, label_text):
        QtWidget.__init__(self)
        QtGui.QLabel.__init__(self, label_text)
        self.error_changed.connect(self._set_error)
        self.setWordWrap(False)

    def set_error(self, is_error):
        """Change the styling of this label according to is_error.

            is_error - True if there is an error with the associated input, False if not.

        Returns nothing."""

        assert type(is_error) is BooleanType, ('is_error must be boolean, '
            '%s found instead' % type(is_error))

        # For some reason, usin this sometimes prints an error message saying 
        # "QPixmap: It is not safe to use pixmaps outside the GUI thread"
        # I'm leaving it alone for now, since the application seems to work ok
        # without it.
        self.error_changed.emit(is_error)


    def _set_error(self, is_error):
        if is_error:
            self.setStyleSheet("QWidget { color: red }")
        else:
            self.setStyleSheet("QWidget {}")

class TextField(QtGui.QLineEdit, QtWidget):
    error_changed = Signal(bool)

    def __init__(self, starting_value):
        QtWidget.__init__(self)
        QtGui.QLineEdit.__init__(self, starting_value)
        self.setMinimumWidth(400)

        # set up my communicator instances and connect them to the correct Qt
        # signals.
        self.value_changed = Communicator()
        self.clicked = Communicator()
        self.textChanged.connect(self._value_changed)
        self.error_changed.connect(self._set_error)

    def mousePressEvent(self, event=None):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(True)
        QtGui.QLineEdit.mousePressEvent(self, event)

    def _value_changed(self, qstring_value):
        """Callback for the TextChanged signal.  Casts to a python string anc
        emits the value_changed communicator signal."""
        qstring_value = self.text()
        new_value = unicode(qstring_value, 'utf-8')
        self.value_changed.emit(new_value)

    def showEvent(self, event=None):
        if len(self.text()) > 0:
            self._value_changed(self.text())

    def set_error(self, is_error):
        """Change the styling of this textfield according to is_error.

            is_error - True if there is an error with the input, False if not.

        Returns nothing."""

        assert type(is_error) is BooleanType, ('is_error must be boolean, '
            '%s found instead' % type(is_error))

        self.error_changed.emit(is_error)

    def _set_error(self, is_error):
        if is_error:
            self.setStyleSheet("QWidget { border: 1px solid red }")
        else:
            self.setStyleSheet("QWidget {}")

    def text(self):
        return QtGui.QLineEdit.text(self)

    def set_text(self, new_value):
        self.setText(new_value)

    def contextMenuEvent(self, event=None):
        """Reimplemented from QtGui.QLineEdit.contextMenuEvent.

        This function allows me to make changes to the context menu when one
        is requested before I show the menu."""
        menu = self.createStandardContextMenu()
        refresh_action = QtGui.QAction(_('Refresh'), menu)
        refresh_action.setIcon(QtGui.QIcon(ICON_REFRESH))
        refresh_action.triggered.connect(self._value_changed)
        menu.addAction(refresh_action)
        menu.exec_(event.globalPos())

class CheckBox(QtGui.QCheckBox, QtWidget):
    error_changed = Signal(bool)
    def __init__(self, label_text):
        QtGui.QCheckBox.__init__(self)
        QtWidget.__init__(self)

        self.setText(label_text)

        self.checkbox_toggled = Communicator()
        self.toggled.connect(self._checkbox_toggled)
        self.error_changed.connect(self._set_error)

    def _checkbox_toggled(self, event=None):
        self.checkbox_toggled.emit(self.isChecked())

    def is_checked(self):
        return self.isChecked()

    def set_checked(self, is_checked):
        assert is_checked in [True, False], ('is_checked must be either True or'
            ' False, %s (%s) found' % (is_checked, type(is_checked)))
        self.setChecked(is_checked)

    def showEvent(self, event):
        # when this checkbox is shown, emit the current checkstate.
        self._checkbox_toggled()

    def set_error(self, is_error):
        assert type(is_error) is BooleanType, ('is_error must be boolean, '
            '%s found instead' % type(is_error))
        # For some reason, usin this sometimes prints an error message saying 
        # "QPixmap: It is not safe to use pixmaps outside the GUI thread"
        # I'm leaving it alone for now, since the application seems to work ok
        # without it.
        self.error_changed.emit(is_error)

    def _set_error(self, is_error):
        # This doesn't work in Qt.  Not sure why.  See this post for someone
        # else with the same idea for styling:
        # http://stackoverflow.com/a/11155163/299084.  I tried the QPalette
        # approach, but that didn't work for me either.
        if is_error:
            self.setStyleSheet("QWidget { color: red }")
        else:
            self.setStyleSheet("QWidget {}")

class FileButton(Button):
    _icon = ICON_FOLDER

    def __init__(self):
        Button.__init__(self)
        self.file_dialog = FileDialog()
        self.clicked.connect(self._get_file)

        self.file_selected = Communicator()

    def _get_file(self):
        filename = self.file_dialog.get_file('file')
        if filename != '':
            self.file_selected.emit(filename)

class FileDialog(QtGui.QFileDialog):
    filters = {
        "all": [_("All files (* *.*)")],
        "EXISTS": [_("All files (* *.*)")],
        "CSV": [_("Comma separated value file (*.csv *.CSV)")],
        "GDAL": [_("[GDAL] Arc/Info Binary Grid (hdr.adf HDR.ADF hdr.ADF)"),
                 _("[GDAL] Arc/Info ASCII Grid (*.asc *.ASC)"),
                 _("[GDAL] GeoTiff (*.tif *.tiff *.TIF *.TIFF)")],
        "OGR": [_("[OGR] ESRI Shapefiles (*.shp *.SHP)")],
        "DBF": [_("[DBF] dBase legacy file (*dbf *.DBF)")],
    }

    def __init__(self):
        QtGui.QFileDialog.__init__(self)
        self.last_filter = QtCore.QString()
        self.last_folder = '~'

    def get_file(self, title):
        default_folder = os.path.expanduser(self.last_folder)
        dialog_title = _('Select ') + title

        filename, filter = self.getOpenFileNameAndFilter(
            self, dialog_title, default_folder, initialFilter=self.last_filter)
        filename = unicode(filename, 'utf-8')
        self.last_filter = filter
        self.last_folder = os.path.dirname(filename)

        return filename

class Dropdown(QtGui.QComboBox, QtWidget):
    def __init__(self, options, default_value):
        QtGui.QComboBox.__init__(self)
        QtWidget.__init__(self)
        for option in options:
            self.addItem(option)

        # create the value_changed communicator and connect the
        # current_index_changed slot.  the slot passes the int index of the new
        # current index, so that should just work as expected.
        self.value_changed = Communicator()
        self.currentIndexChanged.connect(self.value_changed.emit)

        # set the default index
        self.setCurrentIndex(default_value)

    def index(self):
        return self.currentIndex()

    def set_index(self, new_index):
        self.setCurrentIndex(new_index)

class InfoDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.messages = []
        self.resize(400, 200)
        self.setWindowTitle(_('Errors exist!'))
        self.setLayout(QtGui.QVBoxLayout())
        self.icon = QtGui.QLabel()
        self.icon.setStyleSheet('QLabel { padding: 10px }')
        self.set_icon(ICON_ERROR_BIG)
        self.icon.setSizePolicy(QtGui.QSizePolicy.Fixed,
            QtGui.QSizePolicy.Fixed)
        self.title = QtGui.QLabel()
        self.set_title(_('Whoops!'))
        self.title.setStyleSheet('QLabel { font: bold 18px }')
        self.body = QtGui.QLabel()
        self.body.setWordWrap(True)
        self.ok_button = QtGui.QPushButton(_('OK'))
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
        #center_window(self)
        print 'InfoDialog showing'
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
        self.set_title(_('Warning...'))
        self.set_icon(ICON_WARN_BIG)
        self.body.setText(_('Some inputs cannot be validated and may cause ' +
           'this program to fail.  Continue anyways?'))
        self.no_button = QtGui.QPushButton(_('Back'))
        self.no_button.clicked.connect(self.reject)
        self.button_box.addButton(self.no_button, QtGui.QDialogButtonBox.RejectRole)

class ConfirmQuitDialog(WarningDialog):
    def __init__(self):
        WarningDialog.__init__(self)
        self.setWindowTitle(_('Are you sure you want to quit?'))
        self.set_title(_('Really quit?'))
        self.set_icon(ICON_BULB_BIG)
        self.body.setText(_('You will lose any changes to your parameter fields.'))
        self.ok_button.setText(_('Quit'))

class ErrorDialog(InfoDialog):
    def __init__(self):
        InfoDialog.__init__(self)
        self.set_title(_('Whoops!'))

    def showEvent(self, event=None):
        label_string = '<ul>'
        for element_tuple in self.messages:
            label_string += '<li>%s: %s</li>' % element_tuple
        label_string += '</ul>'

        num_messages = len(self.messages)
        if num_messages == 1:
            num_error_string = _('is 1 error')
        else:
            num_error_string = _('are %s errors') % num_messages

        self.body.setText(_(str("There %s that must be resolved" +
            " before this tool can be run:%s")) % (num_error_string, label_string))
        self.body.setMinimumSize(self.body.sizeHint())
        print 'ErrorDialog Showing'
        InfoDialog.showEvent(self, event)

class TabGroup(QtGui.QTabWidget, Group):
    def __init__(self):
        QtGui.QTabWidget.__init__(self)
        Group.__init__(self)

    def add_widget(self, gui_object):
        # gui_object is assumed to be a Tab instance.
        label = gui_object.label()
        if label == '':
            label = _('Tab %s') % self.count()
        self.addTab(gui_object.widgets, label)

    def widgets(self):
        pass

class MessageArea(QtGui.QLabel):
    def __init__(self):
        QtGui.QLabel.__init__(self)
        self.setWordWrap(True)
        self.setTextFormat(QtCore.Qt.RichText)
        self.messages = []

    def clear(self):
        """Clear all text and set the stylesheet to none."""

        self.hide()
        self.setText('')
        self.setStyleSheet('')

    def setText(self, text=None):
        if text == None:
            text = []
        else:
            text = [text + '<br/>']
        messages = text + self.messages
        string = "<br/>".join(messages)
        QtGui.QLabel.setText(self, string)

    def append(self, string):
        self.messages.append(string)
        self.setText()

    def set_error(self, is_error):
        if not is_error:
            self.setStyleSheet('QLabel { padding: 15px;' +
                'background-color: #d4efcc; border: 2px solid #3e895b;}')
        else:
            self.setStyleSheet('QLabel { padding: 15px;' +
                'background-color: #ebabb6; border: 2px solid #a23332;}')
        self.show()

class RealtimeMessagesDialog(QtGui.QDialog):
    """ModelDialog is a class defining a modal window presented to the user
        while the model is running.  This modal window prevents the user from
        interacting with the main UI window while the model is processing and
        provides status updates for the model.

        This window is not configurable through the JSON configuration file."""
    error_changed = Signal(bool)
    message_added = Signal(unicode)

    def __init__(self):
        """Constructor for the ModelDialog class.

            root - a pointer to the parent window

            returns an instance of ModelDialog."""
        QtGui.QDialog.__init__(self)

        #set window attributes
        self.setLayout(QtGui.QVBoxLayout())
        self.setWindowTitle("Running the model")
        self.resize(700, 400)
        center_window(self)
        self.setModal(True)

        self.cancel = False

        #create statusArea-related widgets for the window.        
        self.statusAreaLabel = QtGui.QLabel('Messages:')
        self.statusArea = QtGui.QPlainTextEdit()
        self.statusArea.setReadOnly(True)
        self.cursor = self.statusArea.textCursor()

        #set the background color of the statusArea widget to be white.
        self.statusArea.setStyleSheet("QWidget { background-color: White }")

        #create an indeterminate progress bar.  According to the Qt 
        #documentation, an indeterminate progress bar is created when a 
        #QProgressBar's minimum and maximum are both set to 0.
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setTextVisible(False)

        self.messageArea = MessageArea()
        self.messageArea.clear()

        #Add the new widgets to the window
        self.layout().addWidget(self.statusAreaLabel)
        self.layout().addWidget(self.statusArea)
        self.layout().addWidget(self.messageArea)
        self.layout().addWidget(self.progressBar)


        self.backButton = QtGui.QPushButton(' Back')
        self.backButton.setToolTip('Return to parameter list')

        #add button icons
        self.backButton.setIcon(QtGui.QIcon(ICON_ENTER))

        #disable the 'Back' button by default
        self.backButton.setDisabled(True)

        #create the buttonBox (a container for buttons) and add the buttons to
        #the buttonBox.
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.addButton(self.backButton, QtGui.QDialogButtonBox.AcceptRole)

        #connect the buttons to their callback functions.
        self.backButton.clicked.connect(self.closeWindow)

        #add the buttonBox to the window.        
        self.layout().addWidget(self.buttonBox)

        self.error_changed.connect(self.messageArea.set_error)
        self.message_added.connect(self._write)

    def start(self, event=None):
        self.statusArea.clear()
        self.start_buttons()

        self.write('Initializing...\n')

    def start_buttons(self):
        self.progressBar.setMaximum(0) #start the progressbar.
        self.backButton.setDisabled(True)

    def stop_buttons(self):
        self.progressBar.setMaximum(1) #stops the progressbar.
        self.backButton.setDisabled(False)

    def write(self, text):
        """Write text.  If printing to the status area, also scrolls to the end
            of the text region after writing to it.  This function is
            necessarily thread-safe, thanks to Qt's signal/slot implementation.

            text - a string to be written to self.statusArea.

            returns nothing."""

        self.message_added.emit(text)

    def _write(self, text):
        self.statusArea.insertPlainText(QtCore.QString(text))
        self.cursor.movePosition(QtGui.QTextCursor.End)
        self.statusArea.setTextCursor(self.cursor)

    def flush(self):
        pass

    def finish(self, exception_found, thread_exception=None):
        """Notify the user that model processing has finished.

            returns nothing."""

        self.stop_buttons()
        if exception_found:
            self.messageArea.setText(str('<b>%s</b> encountered: <em>%s</em> <br/>' +
                'See the log for details.') % (thread_exception.__class__.__name__,
                str(thread_exception)))
        else:
            self.messageArea.setText('Model completed successfully.')
        self.error_changed.emit(exception_found)
        self.cursor.movePosition(QtGui.QTextCursor.End)
        self.statusArea.setTextCursor(self.cursor)

    def closeWindow(self):
        """Close the window and ensure the modelProcess has completed.

            returns nothing."""

        self.messageArea.clear()
        self.cancel = False
        self.done(0)

class FormWindow(QtWidget, QtGui.QWidget):
    """A Form is a window where you have a set of inputs that the user fills in
    or configures and then presses 'submit'."""
    def __init__(self, input_pane):
        QtWidget.__init__(self)
        QtGui.QWidget.__init__(self)

        # The form has two elements arranged vertically: the form window (which
        # may eventually need to be scrollable) and the buttonbox.
        self.setLayout(QtGui.QVBoxLayout())

        # create communicators.
        self.submit_pressed = Communicator()
        self.quit_requested = Communicator()

        self.menu_bar = QtGui.QMenuBar()

        # Create the various menus for the window
        self.file_menu = QtGui.QMenu('&File')
        self.load_file_action = self.file_menu.addAction('&Load parameters from file ...')
        self.load_file_action.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        self.save_file_action = self.file_menu.addAction('&Save parameters ...')
        self.save_file_action.setShortcut(QtGui.QKeySequence("Ctrl+S"))
        self.remove_lastrun = self.file_menu.addAction('&Clear cached runs ...')
        self.exit_action = self.file_menu.addAction('Exit')
        self.exit_action.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.menu_bar.addMenu(self.file_menu)

        self.dev_menu = QtGui.QMenu('&Development')
        self.save_to_python = self.dev_menu.addAction('Save to &python script...')
        self.save_to_json = self.dev_menu.addAction('Save to archivable &JSON...')
        self.menu_bar.addMenu(self.dev_menu)
        self.layout().setMenuBar(self.menu_bar)

#        self.exit_action.triggered.connect(self.ui.closeWindow)
#        self.save_file_action.triggered.connect(self.ui.save_parameters_to_file)
#        self.load_file_action.triggered.connect(self.ui.load_parameters_from_file)
#        self.remove_lastrun.triggered.connect(self.ui.remove_lastrun)
#        self.save_to_python.triggered.connect(self.ui.save_to_python)
#        self.save_to_json.triggered.connect(self.ui.save_to_json)


        # Create the QWidget pane for the inputs and add it to the layout.
        self.input_pane = input_pane
        self.input_pane.setFlat(True)
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setWidget(self.input_pane)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().rangeChanged.connect(
            self._update_scroll_border)
        self.layout().addWidget(self.scroll_area)
        self._update_scroll_border(self.scroll_area.verticalScrollBar().minimum(),
            self.scroll_area.verticalScrollBar().maximum())

        # Create the buttonBox and add it to the layout.
        self.run_button = QtGui.QPushButton(_(' Run'))
        self.run_button.setIcon(QtGui.QIcon(os.path.join(ICON_ENTER)))

        self.quit_button = QtGui.QPushButton(_(' Quit'))
        self.quit_button.setIcon(QtGui.QIcon(os.path.join(ICON_CLOSE)))

        self.reset_button = QtGui.QPushButton(_(' Reset'))
        self.reset_button.setIcon(QtGui.QIcon(os.path.join(ICON_UNDO)))

        #create the buttonBox (a container for buttons)
        self.button_box = QtGui.QDialogButtonBox()
        self.button_box.addButton(self.run_button, QtGui.QDialogButtonBox.AcceptRole)
        self.button_box.addButton(self.quit_button, QtGui.QDialogButtonBox.RejectRole)
        self.button_box.addButton(self.reset_button, QtGui.QDialogButtonBox.ResetRole)

        #connect the buttons to their functions.
        self.run_button.clicked.connect(self._run_pressed)
        self.quit_button.clicked.connect(self._quit_pressed)
#        self.reset_button.clicked.connect(self.resetParametersToDefaults)

        #add the buttonBox to the window.
        self.layout().addWidget(self.button_box)
        self.close_confirmed = False

        # adjust the window size.
        screen_geometry = QtGui.QDesktopWidget().availableGeometry()
        screen_width = screen_geometry.width()
        min_width = 800
        if min_width > screen_width:
            width = screen_width - 50
        else:
            width = min_width

        screen_height = screen_geometry.height() * 0.95
        min_height = self.input_pane.minimumSizeHint().height()
        if min_height > screen_height:
            height = screen_height
        else:
            height = min_height

        self.resize(width, height)

    def _update_scroll_border(self, min, max):
        if min == 0 and max == 0:
            self.scroll_area.setStyleSheet("QScrollArea { border: None } ")
        else:
            self.scroll_area.setStyleSheet("")

    def showEvent(self, event):
        center_window(self)
        QtGui.QWidget.showEvent(self, event)

    def _quit_pressed(self):
        if not self.close_confirmed:
            self.quit_requested.emit(True)

    def _run_pressed(self):
        self.submit_pressed.emit(True)

    def close(self):
        # If close() is called, we know for sure that we want to close thw
        # window, no questions asked.
        self.close_confirmed = True
        QtGui.QWidget.close(self)

    def closeEvent(self, event=None):
        self._quit_pressed()

    def add_widget(self, gui_object):
        self.input_pane.add_widget(gui_object)

