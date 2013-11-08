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

class ButtonTest(QtWidgetTest):
    def setUp(self):
        self.widget = qt4.Button()

class InformationButtonTest(ButtonTest):
    def setUp(self):
        self.title = 'Title!'
        self.widget = qt4.InformationButton(self.title)

    def test_setup(self):
        self.assertEqual(self.title, self.widget.title())
        self.assertEqual('', self.widget.body())

    def test_deactivate(self):
        # behavior I care about:
        #  * icon is blank
        #  * element is disabled
        self.assertEqual(self.widget.isEnabled(), True)

        self.widget.deactivate()
        self.assertEqual(self.widget.isEnabled(), False)

class ValidationButtonTest(InformationButtonTest):
    def setUp(self):
        self.title = 'Title!'
        self.widget = qt4.ValidationButton(self.title)

    def test_deactivate(self):
        # overridden from InformationButtonTest, because the validation button
        # is disabled by default.
        self.widget.setEnabled(True)

        # now, run the rest of the test.
        InformationButtonTest.test_deactivate(self)

    def test_set_error_fail(self):
        error_string = 'some error occurred'
        error_state = 'error'

        self.widget.set_error(error_string, error_state)
        self.assertEqual(self.widget.error_text, error_string)
        self.assertEqual(self.widget.error_state, error_state)

    def test_set_error_warning(self):
        error_string = 'some error occurred'
        error_state = 'warning'

        self.widget.set_error(error_string, error_state)
        self.assertEqual(self.widget.error_text, error_string)
        self.assertEqual(self.widget.error_state, error_state)

    def test_set_error_pass(self):
        error_string = 'some error occurred'
        error_state = 'pass'

        self.widget.set_error(error_string, error_state)
        self.assertEqual(self.widget.error_text, error_string)
        self.assertEqual(self.widget.error_state, error_state)

