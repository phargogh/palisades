import unittest

import mock
from PyQt4.QtTest import QTest
from PyQt4 import QtGui

from palisades.gui import qt4
from palisades.gui import core

APPLICATION = qt4.Application()

class QtWidgetTest(unittest.TestCase):
    def setUp(self):
        self.widget = qt4.QtWidget()

    def test_visibility(self):
        # assert widget is visible by default (as long as the widget has been
        # shown).
        self.assertEqual(self.widget.isVisible(), False)
        self.widget.show()
        self.assertEqual(self.widget.isVisible(), True)

        # set widget visibility to False
        self.widget.set_visible(False)
        self.assertEqual(self.widget.isVisible(), False)

        # reset widget visibility and verify change.
        self.widget.set_visible(True)
        self.assertEqual(self.widget.isVisible(), True)

class QtGroupTest(QtWidgetTest):
    class SampleGUI(object):
        def __init__(self):
            self.widgets = [qt4.QtWidget()] * 5

    class SampleLabel(object):
        def __init__(self):
            self.widgets = qt4.QtWidget()

    def setUp(self):
        self.widget = qt4.Group()

    def test_setup(self):
        self.assertEqual(type(self.widget.layout()), type(QtGui.QGridLayout()))

    def test_add_widget(self):
        # verify rowCount is 1 (qt starts with a single row in the gridLayout)
        self.assertEqual(self.widget.layout().rowCount(), 1)

        # add a GUI to the widget and verify there's an extra row.
        self.widget.add_widget(self.SampleGUI())
        self.assertEqual(self.widget.layout().rowCount(), 2)

        # add a GUI with a single widget that spans the whole row
        self.widget.add_widget(self.SampleLabel())
        self.assertEqual(self.widget.layout().rowCount(), 3)

class QtContainerTest(QtGroupTest):
    def setUp(self):
        self.label_text = 'hello there!'
        self.widget = qt4.Container(self.label_text)

    def test_setup(self):
        QtGroupTest.test_setup(self)

        # assert label text is set properly.
        self.assertEqual(self.widget.title(), self.label_text)

        # verify that the container is not collapsible by default.
        self.assertEqual(self.widget.is_collapsible(), False)

    def test_checkbox_toggled(self):
        # assert that when the checkbox is toggled, the signal is emitted.
        mock_func = mock.MagicMock(name='function')
        self.widget.checkbox_toggled.register(mock_func)

        self.assertEqual(self.widget.is_collapsible(), False)
        self.widget.set_collapsible(True)
        self.assertEqual(self.widget.is_collapsible(), True)

        # ensure the checkbox state is changed by setting it to its opposite
        # state.
        self.widget.setChecked(not self.widget.isChecked())
        self.assertEqual(mock_func.called, True)

