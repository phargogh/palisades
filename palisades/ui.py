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


class InformationButton(QtGui.QPushButton):
    _icon = None

    def __init__(self):
        QtGui.QPushButton.__init__(self)
        self.setFlat(True)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        if self._icon is not None:
            self.setIcon(QtGui.QIcon(self._icon))

class ValidationButton(InformationButton):
    pass

class Label(QtGui.QLabel):
    pass

class TextField(QtGui.QLineEdit):
    pass

class FileButton(QtGui.QPushButton):
    pass

class HelpButton(InformationButton):
    _icon = os.path.join(ICONS, 'info.png')

class Text():
    elements = []

    def __init__(self, configuration):
        self._label = Label()
        self._validation_button = ValidationButton()
        self._text_field = TextField()
        self._help_button = HelpButton()

        self._label.setText(configuration['label'])
        self._text_field.setMaximumWidth(configuration['width'])

        self.elements = [
            self._validation_button,
            self._label,
            self._text_field,
            Empty(),
            self._help_button
        ]

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



