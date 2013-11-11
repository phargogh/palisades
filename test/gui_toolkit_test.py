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

    def test_set_active(self):
        # check that I can deactivate/activate the button easily.
        self.assertEqual(self.widget.isEnabled(), True)

        self.widget.set_active(False)
        self.assertEqual(self.widget.isEnabled(), False)

        self.widget.set_active(True)
        self.assertEqual(self.widget.isEnabled(), True)

class InformationButtonTest(ButtonTest):
    def setUp(self):
        self.title = 'Title!'
        self.widget = qt4.InformationButton(self.title)

    def test_setup(self):
        self.assertEqual(self.title, self.widget.title())
        self.assertEqual('', self.widget.body())

class ValidationButtonTest(InformationButtonTest):
    def setUp(self):
        self.title = 'Title!'
        self.widget = qt4.ValidationButton(self.title)

    def test_set_active(self):
        # verify that ButtonTests' set_active works.
        # button is disabled by default, so enable it for the sake of the
        # ButtonTests's test.
        self.widget.setEnabled(True)
        ButtonTest.test_set_active(self)

        # when error state is 'error' or 'warning', button has raised edges
        for state in ['error', 'warning']:
            self.widget.set_error('', state)
            self.widget.set_active(True)
            self.assertEqual(self.widget.isEnabled(), True)
            self.assertEqual(self.widget.isFlat(), False)

        # when error state is 'pass', button is flat
        self.widget.set_error('', 'pass')
        self.widget.set_active(True)
        self.assertEqual(self.widget.isEnabled(), True)
        self.assertEqual(self.widget.isFlat(), True)


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

class LabelTest(QtWidgetTest):
    def setUp(self):
        self.text = 'hello world, this is a label with some text in it.'
        self.widget = qt4.Label(self.text)

    def test_label_contents(self):
        self.assertEqual(self.widget.text(), self.text)

class ElementLabelTest(QtWidgetTest):
    def setUp(self):
        self.text = 'Element label'
        self.widget = qt4.ElementLabel(self.text)

    def test_label_contents(self):
        self.assertEqual(self.widget.text(), self.text)

    def test_set_error_smoke(self):
        self.widget.set_error(True)
        self.widget.set_error(False)

        # verify an assertionError is raised if a boolean is not passed in.
        self.assertRaises(AssertionError, self.widget.set_error, 'False')

class TextFieldTest(QtWidgetTest):
    def setUp(self):
        self.default_value = 'some default value'
        self.widget = qt4.TextField(self.default_value)

    def test_default_value(self):
        self.assertEqual(self.widget.text(), self.default_value)

    def test_set_error_smoke(self):
        self.widget.set_error(True)
        self.widget.set_error(False)

        # verify an assertionError is raised if a boolean is not passed in.
        self.assertRaises(AssertionError, self.widget.set_error, 'False')

    def test_value_changed(self):
        # verify that when the value of the textfield is changed, the
        # value_changed communicator is triggered.
        mock_func = mock.MagicMock(name='function')
        self.widget.value_changed.register(mock_func)

        # verify the mock function has not yet been called.
        self.assertEqual(mock_func.called, False)

        # change the value, verify that mock_func has been called.
        self.widget.set_text('some new value')
        QTest.qWait(50)  # wait for the Qt event loop to detect changed text
        self.assertEqual(self.widget.text(), 'some new value')
        self.assertEqual(mock_func.called, True)

class FileButtonTest(QtWidgetTest):
    def setUp(self):
        self.widget = qt4.FileButton()

    def test_file_selected(self):
        # can't actually get the file dialog's value programmatically, since the
        # function blocks, but I can verify that the file_selected communicator
        # is the correct object.
        self.assertEqual(hasattr(self.widget, 'file_selected'), True)
        self.assertEqual(self.widget.file_selected.__class__.__name__,
            'Communicator')

class DropdownTest(QtWidgetTest):
    def setUp(self):
        self.options = ['a', 'b', 'c']
        self.default_index = 0
        self.widget = qt4.Dropdown(self.options, self.default_index)

    def test_default_options(self):
        num_options = self.widget.count()
        options = [unicode(self.widget.itemText(i), 'utf-8') for i in
            range(num_options)]
        self.assertEqual(options, self.options)

        # assert the default index is set
        self.assertEqual(self.widget.currentIndex(), self.default_index)

    def test_value_changed(self):
        mock_func = mock.MagicMock(name='function')
        self.widget.value_changed.register(mock_func)

        # verify that when the value is set (but not changed), the function is
        # not called.
        self.assertEqual(mock_func.called, False)
        self.widget.setCurrentIndex(self.widget.currentIndex())
        self.assertEqual(mock_func.called, False)

        # when the value is changed, verify that the communicator is called
        new_index = 1
        self.assertNotEqual(self.widget.currentIndex(), new_index)
        self.widget.setCurrentIndex(new_index)
        QTest.qWait(50)  # wait for the qt event loop to catch on
        self.assertEqual(mock_func.called, True)

class CheckboxTest(QtWidgetTest):
    def setUp(self):
        self.label = 'a label here!'
        self.widget = qt4.CheckBox(self.label)

    def test_communicator(self):
        mock_func = mock.MagicMock(name='function')
        self.assertEqual(mock_func.called, False)

        self.widget.checkbox_toggled.register(mock_func)
        self.assertEqual(mock_func.called, False)

        # toggle the checkbox and verify the mock function has been called.
        self.widget.setChecked(not self.widget.isChecked())
        self.assertEqual(mock_func.called, True)

    def test_default_options(self):
        self.assertEqual(self.widget.text(), self.label)
