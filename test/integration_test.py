"""Tests across the several layers of palisades."""
import unittest
import time


class BasicFormInteractivityTest(unittest.TestCase):

    """Test inter-element interactivity in a primitive form."""

    @staticmethod
    def _get_form():
        """Get a primitive palisades form with basic interactivity.

        Creates a simple form with three elements:
            1. An enabling element (folder input) with these signals:
                * Enables element 2
                * Disables element 3
            2. A text input (initially enabled)
            3. A text input (initially disabled)

        Returns:
            An instance of palisades.elements.Form that represents this form.
        """
        from palisades import elements
        palisades_config = {
            'label': 'test for enabledBy replacement',
            'modelName': 'test_enabled_by',
            'targetScript': None,
            'elements': [
                {
                    'id': 'enabling_element',
                    'args_id': 'enabler',
                    'type': 'folder',
                    'validateAs': {'type': 'folder'},
                    'required': True,
                    'signals': [
                        'enables:enabled_element',
                        'disables:disabled_element',
                    ],
                },
                {
                    'id': 'enabled_element',
                    'args_id': 'enabled',
                    'type': 'text',
                    'validateAs': {'type': 'number'},
                    'required': False,
                },
                {
                    'id': 'disabled_element',
                    'args_id': 'disabled',
                    'type': 'text',
                    'validateAs': {'type': 'number'},
                    'required': False,
                    'enabled': True,
                }
            ]
        }

        # Don't need to translate the config, as it's already been translated.
        form = elements.Form(palisades_config)
        form.emit_signals()

        return form

    def test_form_initial_state(self):
        """Assert the initial state of a primitive form."""
        form = BasicFormInteractivityTest._get_form()

        # Assert the initial state
        enabling_element = form.find_element('enabling_element')
        enabled_element = form.find_element('enabled_element')
        disabled_element = form.find_element('disabled_element')
        self.assertTrue(enabling_element.is_enabled())
        self.assertFalse(enabling_element.is_satisfied())
        self.assertFalse(enabled_element.is_enabled())
        self.assertTrue(disabled_element.is_enabled())

    def test_enabling_element(self):
        """Assert enabling affects enabled state."""
        form = BasicFormInteractivityTest._get_form()
        enabling_element = form.find_element('enabling_element')
        enabled_element = form.find_element('enabled_element')

        # Assert that the state changes when the value of the enabler changes
        enabling_element.set_value('/')
        time.sleep(0.1)  # allow validation to complete
        self.assertTrue(enabling_element.is_enabled())
        self.assertTrue(enabling_element.is_satisfied())
        self.assertTrue(enabled_element.is_enabled())

    def test_enabling_gui(self):
        """Assert enabling affects enabled state."""
        import palisades.gui
        form = BasicFormInteractivityTest._get_form()

        gui = palisades.gui.get_application()
        gui.add_window(form)
        enabling_element = gui.find_input('enabling_element')
        enabled_element = gui.find_input('enabled_element')

        # Assert that the state changes when the value of the enabler changes
        enabling_element._text_field.set_text('/')
        time.sleep(0.1)  # allow validation to complete
        self.assertTrue(enabling_element.is_enabled())
        self.assertTrue(enabled_element.is_enabled())

    def test_disabling_elements(self):
        """Assert disabling a single element functions as expected."""
        form = BasicFormInteractivityTest._get_form()

        disabling_element = form.find_element('enabling_element')
        disabled_element = form.find_element('disabled_element')

        # Assert that the state changes when the value of the enabler changes
        disabling_element.set_value('/')
        time.sleep(0.1)  # allow validation to complete
        self.assertTrue(disabling_element.is_enabled())
        self.assertTrue(disabling_element.is_satisfied())
        self.assertFalse(disabled_element.is_enabled())

    def test_disabling_gui(self):
        """Assert disabling a single element works in the GUI."""
        import palisades.gui
        form = BasicFormInteractivityTest._get_form()
        gui = palisades.gui.get_application()
        gui.add_window(form)

        disabling_element = gui.find_input('enabling_element')
        disabled_element = gui.find_input('disabled_element')

        # Assert that the state changes when the value of the enabler changes
        disabling_element._text_field.set_text('/')
        time.sleep(0.1)  # allow validation to complete
        self.assertTrue(disabling_element.is_enabled())
        self.assertFalse(disabled_element.is_enabled())
