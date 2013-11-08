import unittest
import os
import time

from PyQt4.QtTest import QTest

from palisades import elements
from palisades.gui import core

# view for the GUI layer

APPLICATION = core.ApplicationGUI()

class QtTextIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'defaultValue': 'a',
        }
        self.element = elements.Text(config)
        self.gui = core.FileGUI(self.element)

    def test_text_changed(self):
        """Assert element's value when text field value is changed."""
        # assert that the starting value is what we set in the config.
        self.assertEqual(self.element.value(), 'a')

        new_value = 'hello world!'
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

        new_value = 'hello again!'
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

    def test_validation_completed(self):
        """Assert element's validation state when validation completes"""
        # assert that validation state is True by default.
        self.assertEqual(self.gui._validation_button.error_text , '')
        self.assertEqual(self.gui._validation_button.error_state, None)
        self.assertEqual(self.gui._validation_button.isEnabled(), False)
        self.assertEqual(self.element.is_valid(), True)

        # verify that the validation thread has not yet been started
        self.assertEqual(self.element._validator.thread.is_alive(), False)

        # Trigger validation by setting the value of the text.
        self.gui._text_field.setText('new_value')

        # check that the validation thread has been started.
        self.assertRaises(RuntimeError, self.element._validator.thread.start)

        # check the validation state of the element
        self.assertEqual(self.element.is_valid(), True)

        # check the validation state of the GUI.
        self.assertEqual(self.gui._validation_button.error_state, 'pass')

class QtFileIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'defaultValue':  os.getcwd(),
            'validateAs': {
                'type': 'folder',
                'mustExist': True,
            }
        }
        self.element = elements.File(config)
        self.gui = core.FileGUI(self.element)

    def test_set_text(self):
        """Assert element's value when text field value is changed."""
        # assert that the starting value is what we set in the config.
        self.assertEqual(self.element.value(), os.getcwd())

        new_value = os.path.join(os.getcwd(), 'test')
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

        new_value = os.path.join(os.getcwd(), 'palisades')
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

    def test_validation(self):
        """Assert that validation takes place when text is changed."""

        self.assertEqual(self.element.value(), os.getcwd())

        # check the validation state to start out
        self.assertEqual(self.gui._validation_button.error_state, None)
        self.assertEqual(self.element.is_valid(), True)

        # set the textfield value to something else.
        new_value = os.path.join(os.getcwd(), 'test')
        self.element.set_value(new_value)
        self.assertEqual(self.element.value(), new_value)
        self.assertRaises(RuntimeError, self.element._validator.thread.start)
        QTest.qWait(100)
        self.assertEqual(self.element.is_valid(), True)

        # set the textfield value to something that we know will fail validation
        # Need to first verify that the folder that shouldn't exist doesn't.
        new_value = os.path.join(os.getcwd(), 'nonexistent_dir')
        self.assertEqual(os.path.exists(new_value), False)
        self.element.set_value(new_value)
        self.assertRaises(RuntimeError, self.element._validator.thread.start)

        # given the new value, verify that the element failed validation.
        QTest.qWait(100)
        self.assertEqual(self.element.is_valid(), False)

        # verify that the validation button displays the correct error state.
        self.assertEqual(self.gui._validation_button.error_state, 'error')
        self.assertEqual(self.gui._validation_button.isEnabled(), True)
        self.assertNotEqual(self.gui._validation_button.error_text, '')
        self.assertEqual(self.gui._validation_button.isFlat(), False)

    def test_file_button(self):
        """Assert that file selection sets the element value, starts validation"""
        self.assertEqual(self.element.value(), os.getcwd())

        # create a new path and emit the file_selected signal with it.
        # can't actually simulate the mousebutton click here or emit the Qt
        # signal because it will cause the program to present a Qt file dialog
        # and block the program on user input from the file window.
        new_path = os.path.join(os.getcwd(), 'test')
        self.gui._file_button.file_selected.emit(new_path)

        # verify that the new path has been set as the element value and is also
        # the value of the text field.
        QTest.qWait(100)
        self.assertEqual(str(self.gui._text_field.text()), new_path)
        self.assertEqual(self.element.value(), new_path)

class QtDropdownIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'label': 'A Dropdown',
            'options': ['a', 'b', 'c'],
            'defaultValue': 1,
            'returns': 'strings'
        }
        self.element = elements.Dropdown(config)
        self.gui = core.DropdownGUI(self.element)

    def test_setup(self):
        """Assert that the options in the dropdown are correct"""
        # build up a list of entries from the Qt widget.
        qt_options = [str(self.gui._dropdown.itemText(i)) for i in
            range(self.gui._dropdown.count())]

        # assert that the options in the Qt widget are the same as the options
        # specified in the dropdown.
        self.assertEqual(qt_options, ['a', 'b', 'c'])

        # assert the default index
        self.assertEqual(self.element.current_index(), 1, 'default index is not set')
        self.assertEqual(self.gui._dropdown.currentIndex(), 1)

    def test_select_option(self):
        """Assert behavior when user selects an option"""
        # assert the default index is set correctly
        self.assertEqual(self.element.current_index(), 1, 'default index is not set')

        # change the index of the GUI widget and check the element value
        self.gui._dropdown.setCurrentIndex(0)
        QTest.qWait(50)
        self.assertEqual(self.element.current_index(), 0)

class QtContainerIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'label': 'Container!',
            'elements': [
                {
                    'type': 'label',
                    'label': 'hello there!',
                },
                {
                    'type': 'file',
                    'label': 'Select a file',
                },
            ]
        }
        self.element = elements.Container(config)
        self.gui = core.ContainerGUI(self.element)

    def test_setup(self):
        """Assert that the container builds correctly."""
        # assert the correct number of elements in the core container
        self.assertEqual(len(self.element._elements), 2)

        # assert the correct number of rows in the group's layout
        # Qt thinks there's always one extra row, hence the -1.
        self.assertEqual(self.gui.widgets.layout().rowCount() - 1, 2)

        # assert that the default is a non-collapsible container.
        self.assertEqual(self.element.is_collapsible(), False)
        self.assertEqual(self.gui.widgets.isCheckable(), False)

        # when the Container is not collapsible, I should not be able to
        # collapse it.
        self.assertRaises(elements.InteractionError,
            self.element.set_collapsed, True)

    def test_collapsing(self):
        config = {
            'label': 'Container!',
            'collapsible': True,
            'elements': [
                {
                    'type': 'label',
                    'label': 'hello there!',
                },
                {
                    'type': 'file',
                    'label': 'Select a file',
                },
            ]
        }
        self.element = elements.Container(config)
        self.gui = core.ContainerGUI(self.element)

        # assert that when the config defines that the element is collapsible,
        # the widget is indeed collapsible/checkable.
        #TODO: finish this testing!

