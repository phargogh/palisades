from PyQt4 import QtGui
from PyQt4 import QtCore

import palisades

LAYOUTS = {
    palisades.LAYOUT_VERTICAL: QtGui.QVBoxLayout,
    palisades.LAYOUT_HORIZONTAL: QtGui.QHBoxLayout,
    palisades.LAYOUT_GRID: QtGui.QGridLayout,
}

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
        if isinstance(self.layout(), QtGui.QGridLayout):
            for index, sub_element in enumerate(element_ptr.elements):
                if sub_element.sizeHint().isValid():
                    sub_element.setMinimumSize(sub_element.sizeHint())
                self.layout().addWidget(sub_element, self.layout().rowCount(),
                    index)
                print sub_element
        else:
            print self.layout()
            print 'not yet implemented'


class ValidationButton(QtGui.QPushButton):
    pass

class Label(QtGui.QLabel):
    pass

class TextField(QtGui.QLineEdit):
    pass

class FileButton(QtGui.QPushButton):
    pass

class HelpButton(QtGui.QPushButton):
    pass

class Text():
    _validation_button = ValidationButton()
    _label = Label()
    _text_field = TextField()
    _help_button = HelpButton()
    elements = []

    def __init__(self, configuration):
        self.elements = [
            self._validation_button,
            self._label,
            self._text_field,
            Empty(),
            self._help_button
        ]

class File(Text):
    _file_button = FileButton()

    def __init__(self, configuration):
        Text.__init__(self, configuration)
        self.elements = [
            self._validation_button,
            self._label,
            self._text_field,
            self._file_button,
            self._help_button
        ]



