import unittest
import mock

import palisades
from palisades import elements
from palisades.gui import core

class TextGUITest(unittest.TestCase):
    def setUp(self):
        self.application = core.ApplicationGUI()
        self.core_element = elements.Text({})
        self.gui = core.TextGUI(self.core_element)

    def test_set_value(self):
        # verify that when the textfield's value is changed, the element's
        # set_value function is emitted.
        new_value = 'hello world!'
        self.assertNotEqual(self.core_element.value(), new_value)
        self.gui._text_field.value_changed.emit(new_value)
        self.assertEqual(self.core_element.value(), new_value)

