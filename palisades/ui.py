from PyQt4 import QtGui
from PyQt4 import QtCore

class Application():
    app = QtGui.QApplication([''])

class Empty(QtGui.QWidget):
    pass

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

    def __init__(self):
        self.elements = [
            self._validation_button,
            self._label,
            self._text_field,
            Empty(),
            self._help_button
        ]

class File():
    _file_button = FileButton()

    def __init__(self):
        self.elements = [
            self._validation_button,
            self._label,
            self._text_field,
            self._file_button,
            self._help_button
        ]



