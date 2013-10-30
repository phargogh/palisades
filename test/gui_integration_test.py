import unittest

import PyQt4.QtTest as QtTest

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
        self.assertEqual(self.gui._validation_button.error_text , None)
        self.assertEqual(self.gui._validation_button.error_state, 'pass')
        self.assertEqual(self.gui._validation_button.isEnabled(), True)
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
