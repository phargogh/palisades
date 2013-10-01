import unittest
import os

from palisades import elements
from palisades import validation

TEST_DIR = os.path.dirname(__file__)
IUI_CONFIG = os.path.join(TEST_DIR, 'data', 'iui_config')
PALISADES_CONFIG = os.path.join(TEST_DIR, 'data', 'palisades_config')

class ApplicationTest(unittest.TestCase):
    def test_build_application(self):
        ui = elements.Application(os.path.join(PALISADES_CONFIG,
            'timber_clean.json'))
        ui.run()

class ElementTest(unittest.TestCase):
    """This is a base class for the simplest possible element object."""
    def setUp(self):
        self.element = elements.Element({})

    def test_element_enabled(self):
        def check_callback(test_arg):
            """A function to register with the interactivity_changed
            communicator."""
            raise ValueError

        # Ensure the element is enabled by default.
        self.assertEqual(self.element.is_enabled(), True)

        # Disable the element.
        self.element.set_enabled(False)

        # Verify the element is disabled
        self.assertEqual(self.element.is_enabled(), False)

        # Add a callback to the interactivity_changed communicator
        self.element.interactivity_changed.register(check_callback)
        self.assertEqual(self.element.is_enabled(), False)

        # now, re-enable the element and verify that the callback was executed.
        try:
            self.element.set_enabled(True)
            raise AssertionError('Element callbacks were not triggered')
        except ValueError:
            # If the ValueError in check_callback() was raised, this is good!
            # so we continue on to the next check.
            pass

        self.assertEqual(self.element.is_enabled(), True)

    def test_default_config(self):
        def check_config_signal(test_arg):
            """A function to register with the config_changed communicator."""
            raise ValueError

        self.element.config_changed.register(check_config_signal)
        self.assertEqual(self.element._default_config, {})
        self.assertEqual(self.element.config, {})

        new_defaults = {
            'a': 'aaa',
            'b': 'bbb',
        }

        try:
            self.element.set_default_config(new_defaults)
            raise AssertionError('Element callbacks were not triggered')
        except ValueError:
            # If the valueError in check_config_signal was raised, this is good!
            # So we continue on to the next assertion.
            pass
        self.assertEqual(self.element._default_config, new_defaults)
        self.assertEqual(self.element.config, new_defaults)

        new_defaults = {
            'a': 'ccc',
        }
        try:
            self.element.set_default_config(new_defaults)
            raise AssertionError('Element callbacks were not triggered')
        except ValueError:
            # If the valueError in check_config_signal was raised, this is good!
            # So we continue on to the next assertion.
            pass
        self.assertEqual(self.element._default_config, {'a': 'ccc', 'b': 'bbb'})
        self.assertEqual(self.element.config, {'a': 'aaa', 'b': 'bbb'})

class PrimitiveTest(unittest.TestCase):
    def setUp(self):
        self.primitive = elements.Primitive({})

    def test_set_value(self):
        # check that there is no value.
        self.assertEqual(self.primitive.value(), None)

        # Change the value and check that the value has been set
        self.primitive.set_value('aaa')
        self.assertEqual(self.primitive.value(), 'aaa')

        # register a callback
        def sample_callback(event=None):
            raise ValueError
        self.primitive.value_changed.register(sample_callback)

        # change the value and check that the callback was called.
        try:
            self.primitive.set_value('bbb')
            raise AssertionError('Callback was not called')
        except ValueError:
            # The valueError was raised correctly, so we pass.
            pass

    def test_validate(self):
        # Verify that validation has not been performed.
        self.assertEqual(self.primitive.is_valid(), False)

        # Start validation by setting the value.
        self.primitive.set_value('aaa')

        # wait until validation thread finishes (using join())
        # Also need to wait until the primitive's validation Timer object
        # finishes checking on the validator.
        self.primitive._validator.thread.join()
        self.primitive.timer.join()

        # check that validation completed by checking the validity of the input.
        self.assertEqual(self.primitive.is_valid(), validation.V_PASS)

class LabeledPrimitiveTest(unittest.TestCase):
    def setUp(self):
        self.primitive = elements.LabeledPrimitive({'label':'aaa'})

    def test_set_label(self):
        # check that the configuration-defined label is set.
        self.assertEqual(self.primitive.label(), 'aaa')

        # Set the label and check that it was set correctly.
        self.primitive.set_label('abc')
        self.assertEqual(self.primitive.label(), 'abc')

        # verify that the set label is unicode, UTF-8
        label = self.primitive.label()
        self.assertEqual(label.__class__, unicode)
        try:
            label.decode('utf-8')
        except UnicodeError:
            raise AssertionError('label is not UTF-8')

