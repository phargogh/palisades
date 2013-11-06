import unittest
import os
import time

import mock

import palisades
from palisades import elements
from palisades import validation

from PyQt4.QtGui import QApplication

TEST_DIR = os.path.dirname(__file__)
IUI_CONFIG = os.path.join(TEST_DIR, 'data', 'iui_config')
PALISADES_CONFIG = os.path.join(TEST_DIR, 'data', 'palisades_config')

@unittest.skip('no X')
class ApplicationTest(unittest.TestCase):
    def test_build_application_no_gui(self):
        ui = elements.Application(os.path.join(PALISADES_CONFIG,
            'timber_clean.json'))
        self.assertRaises(elements.InvalidData, ui._window.submit)

#    def test_build_application_qt_gui(self):
#        ui = elements.Application(os.path.join(PALISADES_CONFIG,
#            'timber_clean.json'))
#        gui = palisades.gui.build(ui._window)
#        gui.execute()

    @unittest.skip('blocking')
    def test_build_application_qt_gui(self):
        ui = elements.Application(os.path.join(PALISADES_CONFIG,
            'all_elements.json'))
        gui = palisades.gui.build(ui._window)
        gui.execute()

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

    def test_visibility(self):
        # verify that this element is visible and enabled by default.
        self.assertEqual(self.element.is_visible(), True)
        self.assertEqual(self.element.is_enabled(), True)

        # now, disable the element and check visibility.
        self.element.set_enabled(False)
        self.assertEqual(self.element.is_enabled(), False)
        self.assertEqual(self.element.is_visible(), True)

        # re-enable the element and verify it's correct.
        self.element.set_enabled(True)
        self.assertEqual(self.element.is_enabled(), True)
        self.assertEqual(self.element.is_visible(), True)

        # make the element invisible
        self.element.set_visible(False)
        self.assertEqual(self.element.is_enabled(), False)
        self.assertEqual(self.element.is_visible(), False)

        # set the element's enabled state, verify nothing has changed.
        self.element.set_enabled(True)
        self.assertEqual(self.element.is_enabled(), False)
        self.assertEqual(self.element.is_visible(), False)

        self.element.set_enabled(False)
        self.assertEqual(self.element.is_enabled(), False)
        self.assertEqual(self.element.is_visible(), False)

        # make the element visible again, check states
        self.element.set_visible(True)
        self.assertEqual(self.element.is_enabled(), False)
        self.assertEqual(self.element.is_visible(), True)

        # now, create a function and verify it's called when the visibility
        # changes.
        function = mock.MagicMock(name='function')
        self.element.visibility_changed.register(function)
        self.element.set_visible(not self.element.is_visible())
        self.assertEqual(function.called, True)

class PrimitiveTest(ElementTest):
    def setUp(self):
        self.element = elements.Primitive({})

    def test_default_config(self):
        expected_defaults = {
            'validateAs': {'type': 'disabled'},
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_set_value(self):
        # check that there is no value.
        self.assertEqual(self.element.value(), None)

        # Change the value and check that the value has been set
        self.element.set_value('aaa')
        self.assertEqual(self.element.value(), 'aaa')

        # register a callback
        def sample_callback(event=None):
            raise ValueError
        self.element.value_changed.register(sample_callback)

        # change the value and check that the callback was called.
        try:
            self.element.set_value('bbb')
            raise AssertionError('Callback was not called')
        except ValueError:
            # The valueError was raised correctly, so we pass.
            pass

    def test_validate(self):
        # Verify that validation has not been performed.
        # TODO: Should is_valid() be True?
        self.assertEqual(self.element._valid, None)
        self.assertEqual(self.element.is_valid(), True)

        # Start validation by setting the value.
        self.element.set_value('aaa')

        # wait until validation thread finishes (using join())
        self.element._validator.join()

        # check that validation completed by checking the validity of the input.
        self.assertEqual(self.element.is_valid(), True)

    def test_is_valid(self):
        #Verify that element validity works and makes sense.

        # TEST 1:
        # Ensure a new primitive has no value and not valid (due to default
        # validation of "type": "disabled").
        # TODO: should is_valid() be True here?
        self.assertEqual(self.element.value(), None)
        self.assertEqual(self.element.is_valid(), True)

        # TEST2:
        # When no validation is specified in the input dictionary, the default
        # validation is "type: disabled".  Ensure setting the value validates.
        self.element.set_value(4)
        self.assertEqual(self.element.value(), 4)
        self.element._validator.join()
        self.assertEqual(self.element.is_valid(), True)


class LabeledPrimitiveTest(PrimitiveTest):
    def setUp(self):
        self.element = elements.LabeledPrimitive({})

    def test_default_config(self):
        expected_defaults = {
            'label': '',
            'validateAs': {'type': 'disabled'},
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_set_label(self):
        self.element = elements.LabeledPrimitive({'label': 'aaa'})
        # check that the configuration-defined label is set.
        self.assertEqual(self.element.label(), 'aaa')

        # Set the label and check that it was set correctly.
        self.element.set_label('abc')
        self.assertEqual(self.element.label(), 'abc')

        # verify that the set label is unicode, UTF-8
        label = self.element.label()
        assert_utf8(label)

class TextTest(LabeledPrimitiveTest):
    def setUp(self):
        self.element = elements.Text({})

    def test_default_config(self):
        expected_defaults = {
            'width': 60,
            'defaultValue': '',
            'validateAs': {'type': 'string'},
            'label': u'',
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_set_label(self):
        # check that the configuration-defined label is set.
        self.element = elements.Text({'label': 'aaa'})
        self.assertEqual(self.element.label(), 'aaa')

        # Set the label and check that it was set correctly.
        self.element.set_label('abc')
        self.assertEqual(self.element.label(), 'abc')

        # verify that the set label is unicode, UTF-8
        label = self.element.label()
        assert_utf8(label)

    def test_default_value(self):
        element = elements.Text({
            'label': 'text',
            'defaultValue': 'text_element'
        })

        self.assertEqual(element.value(), 'text_element')
        assert_utf8(element.value())

    def test_set_value(self):
        self.element.set_value('new_value')
        self.assertEqual(self.element.value(), 'new_value')
        assert_utf8(self.element.value())

        # verify that even a non-string value is cast to a UTF-8 object.
        self.element.set_value(8)
        self.assertEqual(self.element.value(), '8')
        assert_utf8(self.element.value())

    def test_is_valid(self):
        #Verify that element validity works and makes sense.

        # TEST 1:
        # Ensure a new primitive has no value and not valid (due to default
        # validation of "type": "disabled").
        # TODO: should is_valid() be True here?
        self.assertEqual(self.element.value(), u'')
        self.assertEqual(self.element.is_valid(), True)

        # TEST2:
        # When no validation is specified in the input dictionary, the default
        # validation is "type: disabled".  Ensure setting the value validates.
        self.element.set_value(4)
        self.assertEqual(self.element.value(), unicode(4))
        self.element._validator.join()
        self.assertEqual(self.element.is_valid(), True)

class FileTest(TextTest):
    def setUp(self):
        self.element = elements.File({})

    def test_default_config(self):
        # override from ElementTest
        expected_defaults = {
            'width': 60,
            'defaultValue': '',
            'validateAs': {'type': 'file'},
            'label': u'',
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_validate(self):
        # Verify that validation has not been performed.
        # TODO: Should is_valid() be True?
        self.assertEqual(self.element._valid, None)
        self.assertEqual(self.element.is_valid(), False)

        # Start validation by setting the value.
        # wait until validation thread finishes (using join())
        # check that validation completed by checking the validity of the input.
        self.element.set_value('aaa')
        self.element._validator.join()
        self.assertEqual(self.element.is_valid(), False)

        new_value = os.path.join(os.getcwd(), 'palisades', '__init__.py')
        self.element.set_value(new_value)
        self.element._validator.join()
        self.assertEqual(self.element.is_valid(), True)

    def test_default_value(self):
        # verify the default value is set correctly
        self.assertEqual(self.element.value(), '')

        # now, create a new element and verify its value is set instead.
        new_defaults = {
            'defaultValue': 'text_value',
        }
        test_element = elements.File(new_defaults)
        expected_value = os.path.join(os.getcwd(), new_defaults['defaultValue'])
        self.assertEqual(test_element.value(), expected_value)

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

    def test_set_value_utf8(self):
        # verify that if we set the value with a unicode string,
        # we get a unicode string out
        self.element.set_value(u'aaa')
        returned_string = self.element.value()
        self.assertEqual(type(returned_string), unicode)

    def test_set_value_ascii(self):
        #Verify that if we set the value with an ascii string,
        # we get a unicode string out
        self.element.set_value('aaa')
        returned_string = self.element.value()
        self.assertEqual(type(returned_string), unicode)

    def test_is_valid(self):
        # default validation is for a file, so if we provide a folder, it should
        # fail.
        self.assertEqual(self.element.value(), u'')
        self.assertEqual(self.element.is_valid(), False)

class GroupTest(ElementTest):
    def setUp(self):
        self.element = elements.Group({})
        self.elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]

    def test_default_config(self):
        expected_defaults = {
            'elements': [],
        }
        self.assertEqual(self.element.config, expected_defaults)

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

    def test_new_registrar(self):
        class ExampleClass(object):
            def __init__(self, config):
                pass

        new_registry = {
            'file': ExampleClass
        }
        group = elements.Group({'elements': self.elements}, new_registry)

        # Check out the first element in the Group.  It should be an instance of
        # ExampleClass instead of File, which it was pointing to before.
        self.assertEqual(group._elements[0].__class__.__name__, 'ExampleClass')

        # the other element in this Group should still be the same as it always
        # was
        self.assertEqual(group._elements[1].__class__.__name__, 'Text')

    def test_enable_disable(self):
        config = {
            'elements': self.elements,
        }
        group = elements.Group(config)

        # verify that the Group is enabled by default.
        self.assertEqual(group.is_enabled(), True)

        # verify elements inside the container are all disabled.
        for element in group.elements():
            self.assertEqual(element.is_enabled(), True)

        # now, if we disable the container, it must disable contained elements.
        group.set_enabled(False)
        self.assertEqual(group.is_enabled(), False)
        for element in group.elements():
            self.assertEqual(element.is_enabled(), False,
                "Element %s was not disabled." % element)

    def test_visibility(self):
        # overridden from ElementTest.  Make sure that all tests for Element
        # apply to Group as well.
        ElementTest.test_visibility(self)

        # make sure that I have a Group that has some elements in it.
        self.element = elements.Group({'elements': self.elements})
        self.assertEqual(len(self.element.elements()), 2)
        self.assertEqual(self.element.is_visible(), True)
        self.assertEqual(self.element.is_enabled(), True)

        # verify that when I make the Group invisible, all the contained elements are
        # also made invisible.
        self.element.set_visible(False)
        self.assertEqual(self.element.is_visible(), False)
        self.assertEqual(self.element.is_enabled(), False)
        for element in self.element.elements():
            self.assertEqual(element.is_visible(), False)
            self.assertEqual(element.is_enabled(), False)

        # Make the element visible again and verify it applied to all contained
        # elements.
        self.element.set_visible(True)
        self.assertEqual(self.element.is_visible(), True)
        self.assertEqual(self.element.is_enabled(), True)
        for element in self.element.elements():
            self.assertEqual(element.is_visible(), True)
            self.assertEqual(element.is_enabled(), True)

class ContainerTest(GroupTest):
    def setUp(self):
        self.default_config = {}
        self.element = elements.Container(self.default_config)

        self.elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]

    def test_default_config(self):
        # Override from ElementTest.test_default_config
        expected_defaults = {
            'elements': [],
            'collapsible': False,
            'label': 'Container',
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_display_label(self):
        container_label = "Look!  It's a container!"
        config = {
            'elements': self.elements,
            'label': container_label,
        }
        container = elements.Container(config)

        # check the container's label
        self.assertEqual(container.label(), container_label)

    def test_enabled_defaults(self):
        config = {
            'elements': self.elements,
        }
        container = elements.Container(config)

        # Container should not collapsible by default.
        self.assertEqual(container.is_collapsible(), False)

        # verify the container is not collapsed by default
        self.assertEqual(container.is_collapsed(), False)

        # verify the container cannot be collapsed because it's not collapsible
        self.assertRaises(elements.InteractionError, container.set_collapsed, True)

    def test_collapsability(self):
        config = {
            'elements': self.elements,
            'collapsible': True,
        }
        container = elements.Container(config)

        # verify container is collapsible
        self.assertEqual(container.is_collapsible(), True)

        # verify container is enabled and not collapsed
        self.assertEqual(container.is_enabled(), True)
        self.assertEqual(container.is_collapsed(), False)

        # collapse the conainer and verify all contained elements are disabled
        # Container should still be enabled, but all container elements should
        # not.
        container.set_collapsed(True)
        self.assertEqual(container.is_collapsed(), True)
        self.assertEqual(container.is_enabled(), True)
        for element in container.elements():
            self.assertEqual(element.is_enabled(), False,
                "Element %s was not disabled" % element)

        # re-enable the container and verify all contained elements are
        # re-enabled.
        container.set_collapsed(False)
        self.assertEqual(container.is_collapsed(), False)
        self.assertEqual(container.is_enabled(), True)
        for element in container.elements():
            self.assertEqual(element.is_enabled(), True,
                "Element %s was not re-enabled" % element)

    def test_set_collapsed(self):
        config = {
            "elements": self.elements,
            "collapsible": True,
        }
        container = elements.Container(config)

        self.assertEqual(container.is_collapsed(), False)

        # collapse the container
        container.set_collapsed(True)
        self.assertEqual(container.is_collapsed(), True)

        # re-expand the container
        container.set_collapsed(False)
        self.assertEqual(container.is_collapsed(), False)

    def test_set_collapsed_uncollapsible(self):
        config = {
            "elements": self.elements,
            "collapsible": False,
        }
        container = elements.Container(config)

        self.assertEqual(container.is_collapsed(), False)

        # Verify that we can't collapse the container.
        self.assertRaises(elements.InteractionError, container.set_collapsed,
            True)


class StaticTest(ElementTest):
    def test_static_defaults(self):
        element = elements.Static({})
        self.assertEqual(element.value(), None)

    def test_returns_string(self):
        value = "hello world!"
        element = elements.Static({'returns': value})
        self.assertEqual(element.value(), value)

    def test_returns_dict(self):
        value = {"a":1}
        element = elements.Static({'returns': value})
        self.assertEqual(element.value(), value)

class LabelTest(ElementTest):
    def test_static_defaults(self):
        element = elements.Label({})
        self.assertEqual(element.value(), None)

        self.assertEqual(element.config, {'label': '', 'returns': None})

    def test_returns_string(self):
        value = "hello world!"
        element = elements.Label({'returns': value})
        self.assertEqual(element.value(), value)

    def test_returns_dict(self):
        value = {"a":1}
        element = elements.Label({'returns': value})
        self.assertEqual(element.value(), value)

    def test_label_func(self):
        label_string = 'hello world!'
        config = {
            'label': label_string,
        }
        label_obj = elements.Label(config)

        # assert that the label function gets the correct label string.
        self.assertEqual(label_obj.label(), label_string)

        # assert that there's a default return value as well.
        self.assertEqual(label_obj.value(), None)

    def test_label_and_returns(self):
        label_string = 'hallo Weld!'
        return_value = 'some_value'
        config = {
            'label': label_string,
            'returns': return_value,
        }
        label_obj = elements.Label(config)

        # assert that the label function gets the correct label string
        self.assertEqual(label_obj.label(), label_string)

        # assert that thtere's the correct return value as well
        self.assertEqual(label_obj.value(), return_value)

class DropdownTest(ElementTest):
    def test_defaults(self):
        options = {}
        dropdown = elements.Dropdown(options)
        default_options = {
            'defaultValue': 0,
            'label': u'',
            'options': ['No options specified'],
            'returns': 'strings',
            'validateAs': {'type': 'disabled'},
        }
        self.assertEqual(dropdown._default_config, default_options)
        self.assertEqual(dropdown.options, default_options['options'])
        self.assertEqual(dropdown._value, 0)
        self.assertEqual(dropdown.value(), default_options['options'][0])

    def test_set_value(self):
        """Assert that the correct restrictions are in place on inputs."""
        config = {
            'options': ['a', 'b', 'c'],
        }
        dropdown = elements.Dropdown(config)

        # verify that no selection has yet been made.
        self.assertEqual(dropdown.current_index(), 0)

        # set the value to a legitimate index.
        dropdown.set_value(1)  # 'b', since options is zero-based
        self.assertEqual(dropdown._value, 1)
        self.assertEqual(dropdown.value(), 'b')

        # Try to set the value to an illegitimate index
        self.assertRaises(AssertionError, dropdown.set_value, 'a')
        self.assertRaises(AssertionError, dropdown.set_value, {})
        self.assertRaises(AssertionError, dropdown.set_value,
            len(dropdown.options) + 2)
        self.assertRaises(AssertionError, dropdown.set_value, [])
        self.assertRaises(AssertionError, dropdown.set_value, -1)
        self.assertRaises(AssertionError, dropdown.set_value, -10)

    def test_get_value(self):
        """Assert the correct output value of a Dropdown (strings)"""
        config = {
            'options': ['a', 'b', 'c'],
            'returns': 'strings',
        }
        dropdown = elements.Dropdown(config)

        # verify no selection has yet been made
        self.assertEqual(dropdown.current_index(), 0)

        # when we set the value, get the correct string.
        dropdown.set_value(2)
        self.assertEqual(dropdown.value(), 'c')
        dropdown.set_value(1)
        self.assertEqual(dropdown.value(), 'b')

    def test_get_value_ordinals(self):
        """Assert the correct output value of a Dropdown (ordinals)"""
        config = {
            'options': ['a', 'b', 'c'],
            'returns': 'ordinals',
        }
        dropdown = elements.Dropdown(config)

        # verify no selection has yet been made
        self.assertEqual(dropdown.current_index(), 0)

        # when we set the value, get the correct string.
        dropdown.set_value(2)
        self.assertEqual(dropdown.value(), 2)
        dropdown.set_value(1)
        self.assertEqual(dropdown.value(), 1)

class FormTest(unittest.TestCase):
    def setUp(self):
        self.timber_clean = os.path.join(PALISADES_CONFIG, 'timber_clean.json')
        self.config = {
            'targetScript': os.path.join(TEST_DIR, 'data', 'sample_scripts.py'),
            'elements': [
                {
                    'type': 'folder',
                    'validateAs': {'type': 'folder'},
                    'args_id': 'workspace_dir',
                    'defaultValue': os.path.join(TEST_DIR, 'sample_folder')
                },
                {
                    'type': 'file',
                    'validateAs': {'type': 'file', 'mustExist': True},
                    'args_id': 'timber_shape_uri',
                    'defaultValue': self.timber_clean
                },
                {
                    'type': 'file',
                    'validateAs': {'type': 'file', 'mustExist': True},
                    'defaultValue': self.timber_clean,
                    'args_id': 'attr_table_uri',
                },
                {
                    'type': 'text',
                    'defaultValue': '7',
                    'args_id': 'market_disc_rate',
                }
            ]
        }

    def test_form_creation(self):
        form = elements.Form(self.config)
        form.submit()
        form.runner.executor.join()

