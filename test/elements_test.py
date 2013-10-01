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
#        ui.run()

def assert_utf8(string):
    """Assert that the input string is unicode, formatted as UTF-8."""
    if string.__class__ != unicode:
        raise AssertionError('String is not a unicode object')
    try:
        string.decode('utf-8')
    except UnicodeError:
        raise AssertionError('String is not UTF-8')


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
        assert_utf8(label)

class TextTest(unittest.TestCase):
    def setUp(self):
        self.primitive = elements.Text({'label':'aaa'})

    def test_set_label(self):
        # check that the configuration-defined label is set.
        self.assertEqual(self.primitive.label(), 'aaa')

        # Set the label and check that it was set correctly.
        self.primitive.set_label('abc')
        self.assertEqual(self.primitive.label(), 'abc')

        # verify that the set label is unicode, UTF-8
        label = self.primitive.label()
        assert_utf8(label)

    def test_default_value(self):
        element = elements.Text({
            'label': 'text',
            'defaultValue': 'text_element'
        })

        self.assertEqual(element.value(), 'text_element')
        assert_utf8(element.value())

    def test_set_value(self):
        self.primitive.set_value('new_value')
        self.assertEqual(self.primitive.value(), 'new_value')
        assert_utf8(self.primitive.value())

        # verify that even a non-string value is cast to a UTF-8 object.
        self.primitive.set_value(8)
        self.assertEqual(self.primitive.value(), '8')
        assert_utf8(self.primitive.value())

class FileTest(unittest.TestCase):
    def setUp(self):
        self.element = elements.File({})

    def test_set_value(self):
        # verify that the path set is absolute.
        path = 'a.txt.'
        cwd = os.getcwd()
        self.element.set_value(path)

        self.assertEqual(os.path.isabs(self.element.value()), True)
        self.assertEqual(self.element.value(), os.path.join(cwd, path))
        assert_utf8(self.element.value())

    def test_set_value_userdir(self):
        home_dir = os.path.expanduser('~')
        new_file = 'new.txt'

        self.element.set_value('~/%s' % new_file)
        self.assertEqual(self.element.value(), os.path.join(home_dir, new_file))

class GroupTest(unittest.TestCase):
    def setUp(self):
        self.elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]

    def test_object_creation(self):
        # check that the object has all the correct elements
        group = elements.Group({'elements': self.elements})

        self.assertEqual(len(group._elements), 2)
        self.assertEqual(group._elements[0].__class__, elements.File)
        self.assertEqual(group._elements[1].__class__, elements.Text)

    def test_element_creation(self):
        # Create the group and verify there are no elements.
        group = elements.Group({})
        self.assertEqual(len(group._elements), 0)

        # Create the sample elements and ensure that they are the correct
        # classes and that there are the right number of them.
        group.create_elements(self.elements)
        self.assertEqual(len(group._elements), 2)
        self.assertEqual(group._elements[0].__class__, elements.File)
        self.assertEqual(group._elements[1].__class__, elements.Text)

class FormTest(unittest.TestCase):
    def setUp(self):
        self.form = elements.Form({})

    def test_form_creation(self):
        pass
