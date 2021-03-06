import unittest
import os
import time
import shutil
import tempfile
import logging

import mock

import palisades
from palisades import elements as elements
from palisades import validation

TEST_DIR = os.path.dirname(__file__)
IUI_CONFIG = os.path.join(TEST_DIR, 'data', 'iui_config')
PALISADES_CONFIG = os.path.join(TEST_DIR, 'data', 'palisades_config')

class NullHandler(logging.Handler):
    """A do-nothing handler for logging.

    Very useful for avoiding errors of the 'no handlers could be found for
    logger palisades.elements' variety.
    """
    def emit(self, record):
        pass

_nullhandler = NullHandler()
logging.getLogger('palisades').addHandler(_nullhandler)

@unittest.skip('no X')
class ApplicationTest(unittest.TestCase):
    def setUp(self):
        self.timber_json = os.path.join(PALISADES_CONFIG, 'timber_clean.json')

    def test_build_application_no_gui(self):
        ui = elements.Application(self.timber_json)
        self.assertRaises(elements.InvalidData, ui._window.submit)

    def test_build_application_qt_gui_timber(self):
        ui = elements.Application(self.timber_json)
        gui = palisades.gui.build(ui._window)
        gui.execute()

    def test_build_application_qt_gui_timber_de(self):
        ui = elements.Application(self.timber_json, 'de')
        gui = palisades.gui.build(ui._window)
        gui.execute()

    @unittest.skip('blocking')
    def test_build_application_qt_gui(self):
        ui = elements.Application(os.path.join(PALISADES_CONFIG,
            'all_elements.json'))
        gui = palisades.gui.build(ui._window)
        gui.execute()

    def test_launch_en(self):
        palisades.launch(self.timber_json)

def assert_utf8(string):
    """Assert that the input string is unicode, formatted as UTF-8."""
    if not isinstance(string, unicode):
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

    def test_signals(self):
        # assert that the signals property works as expected.
        expected_signals = ['config_changed', 'interactivity_changed',
            'satisfaction_changed', 'visibility_changed']
        self.assertEqual(sorted(self.element.signals), sorted(expected_signals))

    def test_default_config(self):
        def check_config_signal(test_arg):
            """A function to register with the config_changed communicator."""
            raise ValueError

        self.element.config_changed.register(check_config_signal)
        self.assertEqual(self.element._default_config, {'enabled': True})
        self.assertEqual(self.element.config, {"enabled": True})

        new_defaults = {
            'a': 'aaa',
            'b': 'bbb',
            'enabled': True,
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
        self.assertEqual(self.element._default_config, {'a': 'ccc', 'b': 'bbb',
            "enabled": True})
        self.assertEqual(self.element.config, {'a': 'aaa', 'b': 'bbb',
            "enabled": True})

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

    def test_set_state(self):
        element_cls_name = self.element.__class__.__name__
        if element_cls_name == 'Element':
            self.assertRaises(Exception, self.element.set_state, {})
        else:
            raise AssertionError('test_set_state must be reimplemented')

    def test_get_state(self):
        element_cls_name = self.element.__class__.__name__
        if element_cls_name == 'Element':
            self.assertRaises(Exception, self.element.state)
        else:
            raise AssertionError('test_get_state must be reimplemented')

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, 'dce4f711d1bc0b86ada3d5a7cfdc77f6')

class PrimitiveTest(ElementTest):
    def setUp(self):
        self.element = elements.Primitive({})

    def test_signals(self):
        expected_signals = [
            'config_changed',
            'hidden_toggled',
            'interactivity_changed',
            'satisfaction_changed',
            'validation_completed',
            'validity_changed',
            'value_changed',
            'visibility_changed'
        ]
        self.assertEqual(sorted(self.element.signals), sorted(expected_signals))

    def test_default_config(self):
        expected_defaults = {
            'validateAs': {'type': 'disabled'},
            'hideable': False,
            'enabled': True,
            'required': False,
            'helpText': "",
            'returns': {
                'ifDisabled': False,
                'ifEmpty': False,
                'ifHidden': False,
                'type': 'string',
            }
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

    def test_satisfied(self):
        # Verify that an element is satisfied when it should be.
        # Element is not satisfied to start out.
        self.assertFalse(self.element.is_satisfied())
        self.assertFalse(self.element.has_input())

        # when I set the value to something that will cause validation to pass,
        # the element should be satisfied.
        self.element.set_value('111')
        self.element._validator.join()  # wait until validator finishes
        self.assertTrue(self.element.is_valid())
        self.assertTrue(self.element.has_input())
        self.assertTrue(self.element.is_satisfied())
        self.assertTrue(self.element._satisfied)

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
        # Out put value is a string by default.
        self.element.set_value(4)
        self.assertEqual(self.element.value(), '4')
        self.element._validator.join()
        self.assertEqual(self.element.is_valid(), True)

    def test_get_state(self):
        # verify that the state returns the correct value.
        expected_state = {
            'value': self.element._value, # value() returns strings
            'is_hidden': False,
        }
        self.assertEqual(expected_state, self.element.state())

    def test_set_state(self):
        # verify that setting the state performs as expected.
        new_value = 'some new value'
        self.assertNotEqual(self.element.value(), new_value)
        state = {
            'value': new_value,
            'is_hidden': False,
        }
        self.element.set_state(state)
        self.assertEqual(self.element.value(), new_value)
        self.assertEqual(self.element.is_hidden(), state['is_hidden'])

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '9cba20199e30dca32349e4964271a224')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, '9cba20199e30dca32349e4964271a224')

    def test_required(self):
        self.assertFalse(self.element.is_required())
        self.assertFalse(self.element._conditionally_required)

        # let's artificially set the element to be required
        self.element._required = True
        self.assertTrue(self.element.is_required())

        # now, make the element optional, but set it to be conditionally
        # required
        self.element._required = False
        self.assertFalse(self.element.is_required())
        self.element._conditionally_required = True
        self.assertTrue(self.element.is_required())

class HideablePrimitiveTest(PrimitiveTest):
    def setUp(self):
        self.element = elements.Primitive({'hideable': True})

    def test_default_config(self):
        expected_defaults = {
            'validateAs': {'type': 'disabled'},
            'helpText': '',
            'enabled': True,
            'required': False,
            'hideable': True,
            'returns': {
                'ifDisabled': False,
                'ifEmpty': False,
                'ifHidden': False,
                'type': 'string',
            }
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_get_state(self):
        expected_state = {
            'value': self.element.value(),
            'is_hidden': self.element.is_hidden(),
        }
        self.assertEqual(self.element.state(), expected_state)

    def test_set_state(self):
        expected_state = {
            'value': 'aaa',  # some placeholder value
            'is_hidden': True,
        }
        self.element.set_state(expected_state)
        self.assertEqual(self.element.value(), expected_state['value'])
        self.assertEqual(self.element.is_hidden(), expected_state['is_hidden'])

        new_state = {
            'value': 'bbb',
            'is_hidden': False,
        }
        self.element.set_state(new_state)
        self.assertEqual(self.element.value(), new_state['value'])
        self.assertEqual(self.element.is_hidden(), new_state['is_hidden'])

    def test_get_id(self):
        element_id = self.element.get_id()
        expected_id = "9cba20199e30dca32349e4964271a224"
        self.assertEqual(element_id, expected_id)

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, expected_id)

class LabeledPrimitiveTest(PrimitiveTest):
    def setUp(self):
        self.element = elements.LabeledPrimitive({})

    def test_default_config(self):
        expected_defaults = {
            'label': u'',
            'required': False,
            'helpText': '',
            'enabled': True,
            'returns': {
                'ifDisabled': False,
                'ifEmpty': False,
                'ifHidden': False,
                'type': 'string',
            },
            'validateAs': {'type': 'disabled'},
            'hideable': False,
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

    def test_hidden(self):
        # assert element is not hidden by default
        self.assertEqual(self.element.is_hidden(), False)

        # set the element as hidden, make sure it is.
        self.element.set_hidden(True)
        self.assertEqual(self.element.is_hidden(), True)

        # verify that the hidden_toggled signal is emitted when the hidden state
        # changes.
        function = mock.MagicMock(name='function')
        self.element.hidden_toggled.register(function)

        is_hidden = self.element.is_hidden()
        self.element.set_hidden(not is_hidden)
        self.assertEqual(self.element.is_hidden(), not is_hidden)
        self.assertEqual(function.called, True)

    # TODO: test that when a HideableFileEntry is hidden, the value cannot be
    # retrieved.
    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '581741fc0dabd8652403bb6d8a0f8b19')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, '581741fc0dabd8652403bb6d8a0f8b19')


class TextTest(LabeledPrimitiveTest):
    def setUp(self):
        self.element = elements.Text({})

    def test_default_config(self):
        expected_defaults = {
            'width': 60,
            'defaultValue': '',
            'validateAs': {'type': 'string'},
            'enabled': True,
            'label': u'',
            'helpText': '',
            'required': False,
            'returns': {
                'ifDisabled': False,
                'ifEmpty': False,
                'ifHidden': False,
                'type': 'string',
            },
            'hideable': False,
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
        self.assertEqual(self.element.value(), u'8')
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
        self.assertEqual(self.element.value(), u'4')
        self.element._validator.join()
        self.assertEqual(self.element.is_valid(), True)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, 'cbc4d60d477c32883a589588fdfd4ac9')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, 'cbc4d60d477c32883a589588fdfd4ac9')

    def test_validation_state(self):
        # verify that if we have a validation defn that fails on input, when
        # input is removed, its validity should be cleared as well.
        element = elements.Text({
            'type': 'text',
            'required': False,
            'defaultValue': '',
            'validateAs': {
                'type': 'file',
                'mustExist': True
            },
        })

        # wait until element's validator finishes.
        element._validator.join()
        self.assertTrue(element.is_valid())

        # give the element a file on disk.
        element.set_value(__file__)
        element._validator.join()
        self.assertTrue(element.is_valid())

        # give the element a uri that doesn't exist
        element.set_value('sdfgsd')
        element._validator.join()
        self.assertFalse(element.is_valid())

class FileTest(TextTest):
    def setUp(self):
        self.element = elements.File({})

    def test_default_config(self):
        # override from ElementTest
        expected_defaults = {
            'width': 60,
            'helpText': '',
            'defaultValue': u'',
            'enabled': True,
            'required': False,
            'returns': {
                'ifDisabled': False,
                'ifEmpty': False,
                'ifHidden': False,
                'type': 'string',
            },
            'validateAs': {'type': 'file'},
            'label': u'',
            'hideable': False,
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_validate(self):
        # Verify that validation has not been performed.
        # calling element.is_valid() causes validation to occur.
        self.assertEqual(self.element._valid, None)

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

    def test_satisfied(self):
        # Verify that an element is satisfied when it should be.
        # Element is not satisfied to start out.
        self.assertFalse(self.element.is_satisfied())
        self.assertTrue(self.element.is_enabled())

        # when I set the value to something that will cause validation to pass,
        # the element should be satisfied.
        file_handle, tempfile_uri = tempfile.mkstemp()
        try:
            file_handle.close()
        except:
            pass

        self.element.set_value(tempfile_uri)
        self.element._validator.join()  # wait until validator finishes
        self.assertTrue(self.element.is_valid())
        self.assertTrue(self.element.has_input())
        self.assertTrue(self.element.is_satisfied())
        self.assertTrue(self.element._satisfied)

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
        self.assertEqual(self.element._valid, None)
        self.assertEqual(self.element.is_required(), False)

        # element is valid because there's no input and input is optional.
        self.assertEqual(self.element.is_valid(), True)

        self.element.set_value(os.getcwd())  # set to a dir
        self.assertEqual(self.element.value(), os.getcwd())
        self.assertEqual(self.element.is_valid(), False)

    def test_set_state(self):
        # verify that setting the state performs as expected.
        new_value = '/'
        self.assertNotEqual(self.element.value(), new_value)
        state = {
            'value': new_value,
            'is_hidden': False,
        }
        self.element.set_state(state)
        self.assertEqual(self.element.value(), new_value)
        self.assertEqual(self.element.is_hidden(), state['is_hidden'])

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, 'd783e40c664369d01f7aed0802f5acc0')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, 'd783e40c664369d01f7aed0802f5acc0')

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
            'enabled': True,
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

    def test_get_state(self):
        expected_state = {
            'enabled': self.element.is_enabled(),
        }
        self.assertEqual(self.element.state(), expected_state)


    def test_set_state(self):
        new_state = {
            'enabled': False,
        }
        self.element.set_state(new_state)
        self.assertEqual(self.element.is_enabled(), False)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '26da3d2e0de6c15d2e1931a7345c353f')

class TabTest(GroupTest):
    def setUp(self):
        self.default_config = {}
        self.element = elements.Tab(self.default_config)

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
            'enabled': True,
            'elements': [],
            'label': '',
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '10d129869ca10b1861fa123074f95465')

class TabGroupTest(GroupTest):
    def setUp(self):
        self.default_config = {}
        self.element = elements.TabGroup(self.default_config)

        self.elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]

    def test_create_elements(self):
        # when I create elements in a tabGroup that are not tabs, an
        # AssertionError should be raised.
        self.assertRaises(AssertionError, self.element.create_elements,
            self.elements)

        # when I create elements in a TabGroup that are all tabs, they should
        # create just fine.
        tabs = [{'type': 'tab'}, {'type': 'tab'}]
        self.element.create_elements(tabs)
        self.assertEqual(len(self.element.elements()), 2)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '6fa33e1076f00ab0377683511042b3b1')

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

    def test_signals(self):
        expected_signals = [
            'config_changed',
            'interactivity_changed',
            'satisfaction_changed',
            'toggled',
            'visibility_changed'
        ]
        self.assertEqual(sorted(self.element.signals), sorted(expected_signals))

    def test_default_config(self):
        # Override from ElementTest.test_default_config
        expected_defaults = {
            'elements': [],
            'defaultValue': True,
            'collapsible': False,
            'enabled': True,
            'label': '',
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_display_label(self):
        # check the container's label is the default value.
        self.assertEqual(self.element.label(), '')

    def test_enabled_defaults(self):
        # Container should not collapsible by default.
        self.assertEqual(self.element.is_collapsible(), False)

        # verify the container is not collapsed by default
        self.assertEqual(self.element.is_collapsed(), False)

        # verify the container cannot be collapsed because it's not collapsible
        self.assertRaises(elements.InteractionError, self.element.set_collapsed, True)

    def test_collapsability(self):
        # to make the container collapsible after the config, I set the private
        # collapsible variable to True.
        self.element._collapsible = True

        # I want to creat a couple elements after the fact to better simulate
        # collapsibility, and verify that the correct number of elements have
        # been created.
        self.element.create_elements(self.elements)
        self.assertEqual(len(self.element.elements()), 2)

        # verify container is collapsible
        self.assertEqual(self.element.is_collapsible(), True)

        # verify self.element is enabled and not collapsed
        self.assertEqual(self.element.is_enabled(), True)
        self.assertEqual(self.element.is_collapsed(), False)

        # collapse the conainer and verify all contained elements are disabled
        # Container should still be enabled, but all container elements should
        # not.
        self.element.set_collapsed(True)
        self.assertEqual(self.element.is_collapsed(), True)
        self.assertEqual(self.element.is_enabled(), True)
        for element in self.element.elements():
            self.assertEqual(element.is_enabled(), False,
                "Element %s was not disabled" % element)

        # re-enable the container and verify all contained elements are
        # re-enabled.
        self.element.set_collapsed(False)
        self.assertEqual(self.element.is_collapsed(), False)
        self.assertEqual(self.element.is_enabled(), True)
        for element in self.element.elements():
            self.assertEqual(element.is_enabled(), True,
                "Element %s was not re-enabled" % element)

    def test_set_collapsed(self):
        # to make the container collapsible after creation (definitely not
        # kosher), I set the correct variable.
        self.element._collapsible = True

        self.assertEqual(self.element.is_collapsed(), False)

        # collapse the container
        self.element.set_collapsed(True)
        self.assertEqual(self.element.is_collapsed(), True)

        # re-expand the container
        self.element.set_collapsed(False)
        self.assertEqual(self.element.is_collapsed(), False)

    def test_set_collapsed_uncollapsible(self):
        # the default collapsibility should be False.
        self.assertEqual(self.element.is_collapsed(), False)

        # Verify that we can't collapse the container.
        with self.assertRaises(elements.InteractionError):
            self.element.set_collapsed(True)

    def test_satisfaction_based_on_enabled_state(self):
        from palisades import elements
        config = {
            'enabled': True,
            'label': False,
            'collapsible': False,
        }
        container = elements.Container(config)

        self.assertTrue(container.is_enabled())
        self.assertTrue(container.is_satisfied())

        # disable the container; satisfaction, enabled state should change.
        container.set_enabled(False)
        self.assertFalse(container.is_enabled())
        self.assertFalse(container.is_satisfied())

    def test_satisfaction_based_on_enabled_state_collapsible(self):
        from palisades import elements
        config = {
            'enabled': True,
            'label': False,
            'collapsible': True,
        }
        container = elements.Container(config)

        self.assertTrue(container.is_enabled())
        self.assertTrue(container.is_satisfied())

        # disable the container; satisfaction, enabled state should change.
        container.set_enabled(False)
        self.assertFalse(container.is_enabled())
        self.assertFalse(container.is_satisfied())

    def test_satisfaction_based_on_collapsed_state(self):
        from palisades import elements
        config = {
            'enabled': True,
            'label': False,
            'collapsible': True,
            'elements': [],
        }
        container = elements.Container(config)

        self.assertFalse(container.is_collapsed())
        self.assertTrue(container.is_satisfied())

        # Collapse the container, satisfaction should change.
        container.set_collapsed(True)
        self.assertTrue(container.is_collapsed())
        self.assertFalse(container.is_satisfied())

    def test_satisfaction_based_on_collapsed_state_initially_collapsed(self):
        from palisades import elements
        config = {
            'enabled': True,
            'label': False,
            'collapsible': True,
            'defaultValue': False,
            'elements': [],
        }
        container = elements.Container(config)

        self.assertTrue(container.is_collapsed())
        self.assertFalse(container.is_satisfied())

        # Collapse the container, satisfaction should change.
        container.set_collapsed(False)
        self.assertFalse(container.is_collapsed())
        self.assertTrue(container.is_satisfied())

    def test_get_state(self):
        expected_state = {
            'enabled': self.element.is_enabled(),
            'collapsed': self.element.is_collapsed(),
        }
        self.assertEqual(self.element.state(), expected_state)


    def test_set_state(self):
        new_state = {
            'enabled': False,
            'collapsed': False,
        }
        self.element.set_state(new_state)
        self.assertEqual(self.element.is_enabled(), False)
        self.assertEqual(self.element.is_collapsed(), False)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '49b77b1e66870317bc5969720f2a58b4')

class MultiTest(ContainerTest):
    def setUp(self):
        self.elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]
        self.element = elements.Multi({})

    def test_signals(self):
        expected_signals = [
            'config_changed',
            'element_added',
            'element_removed',
            'interactivity_changed',
            'satisfaction_changed',
            'toggled',
            'visibility_changed'
        ]
        self.assertEqual(sorted(self.element.signals), sorted(expected_signals))

    def test_default_config(self):
        expected_defaults = {
            'label': '',
            'helpText': '',
            'enabled': True,
            'defaultValue': [],
            'collapsible': False,
            'elements': [],
            'link_text': 'Add another',
            'return_type': 'list',
            'template': {
                'width': 60,
                'defaultValue': '',
                'enabled': True,
                'helpText': '',
                'hideable': False,
                'required': False,
                'returns': {
                    'ifDisabled': False,
                    'ifHidden': False,
                    'ifEmpty': False,
                    'type': 'string',
                },
                'type': 'text',
                'label': 'Input a number',
                'validateAs': {'type': 'disabled'},
            },
        }
        self.maxDiff = None
        self.assertEqual(self.element.config, expected_defaults)

        # verify that there are no elements by default, until the user creates
        # some by way of the template.
        self.assertEqual(len(self.element.elements()), 0)

    def test_display_label(self):
        self.assertEqual(self.element.label(), '')

    def test_add_element(self):
        # verify that there are no elements by default.
        self.assertEqual(len(self.element.elements()), 0)

        # when I call add_element, I should see a new Text element appear in
        # elements().
        self.element.add_element()
        self.assertEqual(len(self.element.elements()), 1)
        self.assertEqual(self.element.elements()[0].__class__.__name__, 'Text')

        # create a mock function and make sure that it's called when an element
        # is created by add_element and that it was called with the correct
        # argument.
        add_elem_func = mock.MagicMock()
        self.element.element_added.register(add_elem_func)
        self.element.add_element()
        self.assertEqual(add_elem_func.called, True)
        add_elem_func.assert_called_with(1)
        self.assertEqual(len(self.element.elements()), 2)

        self.element.add_element()
        self.assertEqual(len(self.element.elements()), 3)
        add_elem_func.assert_called_with(2)

    def test_remove_element(self):
        # verify there are no elements by default.
        self.assertEqual(len(self.element.elements()), 0)

        # create two new elements.
        # test_add_elements tests that the elements are correct.  This test
        # assumes that add_element works properly.
        for i in range(3):
            self.element.add_element()

        remove_elem_func = mock.MagicMock()
        self.element.element_removed.register(remove_elem_func)
        self.element.remove_element(1)
        remove_elem_func.assert_called_with(1)
        self.assertEqual(len(self.element.elements()), 2)

    def test_value(self):
        # add a couple of default elements
        self.element.add_element()
        self.element.add_element()

        # verify that we're getting the correct, blank list of values back
        self.assertEqual(self.element.value(), ['', ''])

        # set the value of the individual contained elements and verify that
        # the value of the multi element has changed.
        self.element._elements[0].set_value('aaa')
        self.element._elements[1].set_value('bbb')
        self.assertEqual(self.element.value(), ['aaa', 'bbb'])

    def test_value_nested_containers_list(self):
        nested_multi = elements.Multi({
            "type": "multi",
            "template":{
                "type": "container",
                "elements": [
                    {
                        "type": "text",
                        "defaultValue": "aaa",
                    },
                    {
                        "type": "container",
                        "elements": [
                            {
                                "type": "text",
                                "defaultValue": "bbb",
                            },
                        ]
                    }
                ]
            }
        })

        nested_multi.add_element()
        self.assertEqual(len(nested_multi._elements), 1)
        self.assertEqual(nested_multi.value(), [['aaa', ['bbb']]])

        nested_multi.add_element()
        self.assertEqual(len(nested_multi._elements), 2)
        self.assertEqual(nested_multi.value(), [['aaa', ['bbb']], ['aaa',
            ['bbb']]])

    def test_value_nested_containers_dict(self):
        nested_multi = elements.Multi({
            "type": "multi",
            "return_type": "dict",
            "template":{
                "type": "container",
                "elements": [
                    {
                        "type": "text",
                        "defaultValue": "aaa",
                        'args_id': 'aaa',
                    },
                    {
                        "type": "container",
                        "args_id": "container",
                        "elements": [
                            {
                                "type": "text",
                                "defaultValue": "bbb",
                                'args_id': 'bbb',
                            },
                        ]
                    }
                ]
            }
        })
        nested_multi.add_element()

        expected_value = [{
            "container": {
                'bbb': 'bbb',
            },
            'aaa': 'aaa',
        }]
        self.assertEqual(nested_multi.value(), expected_value)

    def test_set_collapsed_uncollapsible(self):
        multi = elements.Multi({})

        # the default collapsibility should be False.
        self.assertEqual(multi.is_collapsed(), False)

        # Verify that we can't collapse the container.
        with self.assertRaises(elements.InteractionError):
            multi.set_collapsed(True)

    def test_get_state(self):
        expected_state = {
            'enabled': self.element.is_enabled(),
            'collapsed': self.element.is_collapsed(),
            'value': [],
        }
        self.assertEqual(self.element.state(), expected_state)

    def test_set_state(self):
        multi = elements.Multi({'collapsible': True})
        new_state = {
            'enabled': False,
            'collapsed': False,
            'value': [],
        }
        multi.set_state(new_state)
        self.assertEqual(multi.is_enabled(), False)
        self.assertEqual(multi.is_collapsed(), False)
        self.assertEqual(len(multi.elements()), 0)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '027588c3492fd9dda1342862158ba3f6')

    def test_set_collapsed(self):
        # MultiElements are not collapsible.
        with self.assertRaises(elements.InteractionError):
            self.element.set_collapsed(False)

    def test_collapsability(self):
        self.assertFalse(self.element.is_collapsible())


class StaticTest(ElementTest):
    def setUp(self):
        self.element = elements.Static({})

    def test_signals(self):
        expected_signals = [
            'config_changed',
            'hidden_toggled',
            'interactivity_changed',
            'satisfaction_changed',
            'validation_completed',
            'validity_changed',
            'value_changed',
            'visibility_changed'
        ]
        self.assertEqual(sorted(self.element.signals), sorted(expected_signals))

    def test_default_config(self):
        expected_defaults = {
            'returnValue': None,
            'enabled': True,
            'hideable': False,
            'required': False,
            'validateAs': {'type': 'disabled'},
        }
        self.assertEqual(expected_defaults, self.element.config)

    def test_static_defaults(self):
        element = elements.Static({})
        self.assertEqual(element.value(), None)

    def test_returns_string(self):
        value = "hello world!"
        element = elements.Static({'returnValue': value})
        self.assertEqual(element.value(), value)

    def test_returns_dict(self):
        value = {"a":1}
        element = elements.Static({'returnValue': value})
        self.assertEqual(element.value(), value)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, 'd5075c3e868b9b76ae2bce70de38696e')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, 'd5075c3e868b9b76ae2bce70de38696e')

    def test_get_state(self):
        # nothing to test, since there's no relevant state.
        pass

    def test_set_state(self):
        # nothing to test, since there's no relevant state.
        pass

class LabelTest(ElementTest):
    def setUp(self):
        self.element = elements.Label({})

    def test_signals(self):
        expected_signals = [
            'config_changed',
            'hidden_toggled',
            'interactivity_changed',
            'label_changed',
            'satisfaction_changed',
            'styles_changed',
            'validation_completed',
            'validity_changed',
            'value_changed',
            'visibility_changed'
        ]
        self.assertEqual(sorted(self.element.signals), sorted(expected_signals))

    def test_default_config(self):
        expected_defaults = {
            'label': '',
            'returnValue': None,
        }

    def test_static_defaults(self):
        element = elements.Label({})
        self.assertEqual(element.value(), None)

        expected_config = {
            'label': '',
            'returnValue': None,
            'enabled': True,
            'hideable': False,
            'required': False,
            'validateAs': {'type': 'disabled'},
            'style': None,
        }

        self.assertEqual(element.config, expected_config)

    def test_returns_string(self):
        value = "hello world!"
        element = elements.Label({'returnValue': value})
        self.assertEqual(element.value(), value)

    def test_returns_dict(self):
        value = {"a":1}
        element = elements.Label({'returnValue': value})
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
            'returnValue': return_value,
        }
        label_obj = elements.Label(config)

        # assert that the label function gets the correct label string
        self.assertEqual(label_obj.label(), label_string)

        # assert that thtere's the correct return value as well
        self.assertEqual(label_obj.value(), return_value)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '303f45c98833f41625e27a54e5574bbe')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, '303f45c98833f41625e27a54e5574bbe')

    def test_get_state(self):
        # nothing to test, since there's no relevant state.
        pass

    def test_set_state(self):
        # nothing to test, since there's no relevant state.
        pass

class DropdownTest(LabeledPrimitiveTest):
    def setUp(self):
        self.element = elements.Dropdown({})

    def test_signals(self):
        expected_signals = [
            'config_changed',
            'hidden_toggled',
            'interactivity_changed',
            'options_changed',
            'satisfaction_changed',
            'validation_completed',
            'validity_changed',
            'value_changed',
            'visibility_changed'
        ]
        self.assertEqual(sorted(self.element.signals), sorted(expected_signals))

    def test_default_config(self):
        expected_defaults = {
            'defaultValue': 0,
            'label': u'',
            'options': ['No options specified'],
            'returns': {
                'type': 'string',
                'ifDisabled': False,
                'ifEmpty': False,
                'ifHidden': False,
            },
            'required': False,
            'helpText': '',
            'validateAs': {'type': 'disabled'},
            'enabled': True,
            'hideable': False,
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_defaults(self):
        options = {}
        dropdown = elements.Dropdown(options)
        default_options = {
            'defaultValue': 0,
            'label': u'',
            'helpText': '',
            'options': ['No options specified'],
            'returns': {
                'type': 'string',
                'ifEmpty': False,
                'ifHidden': False,
                'ifDisabled': False,
            },
            'required': False,
            'validateAs': {'type': 'disabled'},
            'enabled': True,
            'hideable': False,
        }
        self.assertEqual(dropdown._default_config, default_options)
        self.assertEqual(dropdown.options, default_options['options'])
        self.assertEqual(dropdown._value, 0)
        self.assertEqual(dropdown.value(), default_options['options'][0])

    def test_satisfied(self):
        # Verify that an element is satisfied when it should be.
        # Element is not satisfied to start out.
        self.assertFalse(self.element.is_satisfied())

        # when I set the value to something that will cause validation to pass,
        # the element should be satisfied.
        self.element.set_value(0)
        self.element._validator.join()  # wait until validator finishes
        self.assertTrue(self.element.is_valid())
        self.assertTrue(self.element.has_input())
        self.assertTrue(self.element.is_satisfied())
        self.assertTrue(self.element._satisfied)

    def test_set_value(self):
        """Assert that the correct restrictions are in place on inputs."""
        config = {
            'options': ['a', 'b', 'c'],
            'returns': {'type': 'string'},
        }
        dropdown = elements.Dropdown(config)

        # verify that no selection has yet been made.
        self.assertEqual(dropdown.current_index(), 0)

        # set the value to a legitimate index.
        dropdown.set_value(1)  # 'b', since options is zero-based
        self.assertEqual(dropdown._value, 1)
        self.assertEqual(dropdown.value(), 'b')

        # Try to set the value to an illegitimate index
        self.assertRaises(AssertionError, dropdown.set_value, 'z')
        self.assertRaises(AssertionError, dropdown.set_value, {})
        self.assertRaises(AssertionError, dropdown.set_value,
            len(dropdown.options) + 2)
        self.assertRaises(AssertionError, dropdown.set_value, [])
        self.assertRaises(AssertionError, dropdown.set_value, -2)
        self.assertRaises(AssertionError, dropdown.set_value, -10)

    def test_get_value(self):
        """Assert the correct output value of a Dropdown (strings)"""
        config = {
            'options': ['a', 'b', 'c'],
            'returns': {'type': 'string'},
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
            'returns': {'type': 'ordinal'},
        }
        dropdown = elements.Dropdown(config)

        # verify no selection has yet been made
        self.assertEqual(dropdown.current_index(), 0)

        # when we set the value, get the correct string.
        dropdown.set_value(2)
        self.assertEqual(dropdown.value(), 2)
        dropdown.set_value(1)
        self.assertEqual(dropdown.value(), 1)

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, '3d498b434dc5a1d10e483c9b1f942dcd')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, '3d498b434dc5a1d10e483c9b1f942dcd')

    def test_is_valid(self):
        #Reimplementing here because values are specific to Dropdown.
        #Verify that element validity works and makes sense.


        # TEST 1:
        # Ensure a new primitive has no value and not valid (due to default
        # validation of "type": "disabled").
        # TODO: should is_valid() be True here?
        self.assertEqual(self.element.value(), 'No options specified')
        self.assertEqual(self.element.is_valid(), True)

        # TEST2:
        # When no validation is specified in the input dictionary, the default
        # validation is "type: disabled".  Ensure setting the value validates.
        element_config = {
            'options': ['a', 'b', 'c'],
        }
        element = elements.Dropdown(element_config)

        element.set_value(1)
        self.assertEqual(element.value(), 'b')
        element._validator.join()
        self.assertEqual(element.is_valid(), True)

    def test_validate(self):
        # reimplementing here because of datatype restrictions for Dropdown

        # Verify that validation has not been performed.
        # TODO: Should is_valid() be True?
        self.assertEqual(self.element._valid, None)
        self.assertEqual(self.element.is_valid(), True)

        # Start validation by setting the value.
        self.element.set_value(0)

        # wait until validation thread finishes (using join())
        self.element._validator.join()

        # check that validation completed by checking the validity of the input.
        self.assertEqual(self.element.is_valid(), True)

    def test_set_state(self):
        # verify that setting the state performs as expected.
        new_value = 0
        self.assertNotEqual(self.element.value(), new_value)
        state = {
            'value': new_value,
            'is_hidden': True,
        }
        self.element.set_state(state)
        self.assertEqual(self.element.value(), 'No options specified')


class CheckBoxTest(LabeledPrimitiveTest):
    def setUp(self):
        self.element = elements.CheckBox({})

    def test_default_config(self):
        expected_defaults = {
            'label': u'',
            'required': False,
            'helpText': '',
            'enabled': True,
            'returns': {
                'ifDisabled': False,
                'ifEmpty': True,
                'ifHidden': False,
                'type': 'bool',
            },
            'validateAs': {'type': 'disabled'},
            'hideable': False,
        }
        self.assertEqual(self.element.config, expected_defaults)

    def test_satisfied(self):
        # Verify that an element is satisfied when it should be.
        # Element is not satisfied to start out.
        self.assertFalse(self.element.is_satisfied())

        # when I set the value to something that will cause validation to pass,
        # the element should be satisfied.
        self.element.set_value(True)
        self.element._validator.join()  # wait until validator finishes
        self.assertTrue(self.element.is_valid())
        self.assertTrue(self.element.has_input())
        self.assertTrue(self.element.is_satisfied())
        self.assertTrue(self.element._satisfied)

    def test_set_value(self):
        # overridden from PrimitiveTest.set_value(), since the values for a
        # checkbox are boolean.

        # check that there is no value.
        self.assertEqual(self.element.value(), False)

        # Change the value and check that the value has been set
        self.element.set_value(True)
        self.assertEqual(self.element.value(), True)

        # register a callback
        def sample_callback(event=None):
            raise ValueError
        self.element.value_changed.register(sample_callback)

        # change the value and check that the callback was called.
        try:
            self.element.set_value(False)
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
        self.element.set_value(True)

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
        self.assertEqual(self.element.value(), False)
        self.assertEqual(self.element.is_valid(), True)

        # TEST2:
        # When no validation is specified in the input dictionary, the default
        # validation is "type: disabled".  Ensure setting the value validates.
        self.element.set_value(True)
        self.assertEqual(self.element.value(), True)
        self.element._validator.join()
        self.assertEqual(self.element.is_valid(), True)

    def test_set_state(self):
        # verify that setting the state performs as expected.
        new_value = True
        self.assertNotEqual(self.element.value(), new_value)
        state = {
            'value': new_value,
            'is_hidden': True,
        }
        self.element.set_state(state)
        self.assertEqual(self.element.value(), new_value)
        self.assertEqual(self.element.is_hidden(), state['is_hidden'])

    def test_get_id(self):
        element_id = self.element.get_id()
        self.assertEqual(element_id, 'e3ea1643e88dc2f1390de791149f79ed')

        # assert that the element's ID has not changed following
        # validation
        self.element.validate()
        self.element._validator.join()
        self.assertEqual(element_id, 'e3ea1643e88dc2f1390de791149f79ed')

class FormTest(unittest.TestCase):
    def setUp(self):
        self.timber_clean = os.path.join(PALISADES_CONFIG, 'timber_clean.json')
        self.config = {
            'modelName': 'Example_script',
            'targetScript': os.path.join(TEST_DIR, 'data', 'sample_scripts.py'),
            'elements': [
                {
                    'id': 'workspace',
                    'type': 'folder',
                    'validateAs': {'type': 'folder'},
                    'args_id': 'workspace_dir',
                    'defaultValue': os.path.join(TEST_DIR, 'sample_folder')
                },
                {
                    'id': 'file_1',
                    'type': 'file',
                    'validateAs': {'type': 'file', 'mustExist': True},
                    'args_id': 'timber_shape_uri',
                    'defaultValue': self.timber_clean
                },
                {
                    'id': 'file_2',
                    'type': 'file',
                    'validateAs': {'type': 'file', 'mustExist': True},
                    'defaultValue': self.timber_clean,
                    'args_id': 'attr_table_uri',
                },
                {
                    'id': 'text_1',
                    'type': 'text',
                    'defaultValue': '7',
                    'args_id': 'market_disc_rate',
                },
                {
                    'type': 'text',
                    'defaultValue': '8'
                }
            ]
        }
        self.form = elements.Form(self.config)
        self.maxDiff = None
        self.workspace = self.config['elements'][0]['defaultValue']

    def tearDown(self):
        try:
            shutil.rmtree(self.workspace)
        except OSError:
            pass

    def test_collect_arguments(self):
        expected_args = {
            'workspace_dir': os.path.join(TEST_DIR, 'sample_folder'),
            'timber_shape_uri': self.timber_clean,
            'attr_table_uri': self.timber_clean,
            'market_disc_rate': '7',
        }
        returned_args = self.form.collect_arguments()
        self.assertEqual(returned_args, expected_args)

        expected_args = {
            'workspace_dir': os.path.join(TEST_DIR, 'sample_folder'),
            'timber_shape_uri': self.timber_clean,
            'market_disc_rate': u'7',
        }
        # disable the attr_table_uri element and verify that its value was not
        # in the returned dictionary.
        # we know that it's element index 2 because that's the order in which it
        # was created.
        self.form.elements[2].set_enabled(False)
        self.assertEqual(self.form.elements[2].is_enabled(), False)
        self.assertEqual(self.form.elements[2].should_return(), False)
        returned_args = self.form.collect_arguments()
        self.assertEqual(returned_args, expected_args)


    def test_form_creation(self):
        form = elements.Form(self.config)
        form.submit()
        form.runner.executor.join()

    def test_form_is_valid(self):
        # form should be valid by default.
        self.assertEqual(self.form.form_is_valid(), True)

        # make one of the elements fail.
        self.form.elements[2].set_value('lkjahdflg')
        self.assertEqual(self.form.elements[2].is_valid(), False)
        self.assertEqual(self.form.form_is_valid(), False)

    def test_form_errors(self):
        self.assertEqual(self.form.form_is_valid(), True)
        self.assertEqual(self.form.form_errors(), [])

        # make one of the elements fail.
        self.form.elements[2].set_value('lkjahdflg')
        self.assertEqual(self.form.elements[2].is_valid(), False)
        self.assertEqual(len(self.form.form_errors()), 1)

    def test_save_to_python_smoke(self):
        # just verify that the function will run with the correct attributes.
        out_file = 'test.txt'
        self.form.save_to_python(out_file)
        os.remove(out_file)

    def test_element_communication_json(self):
        # build up a form with the appropriate communication JSON
        pass

    def test_element_communication_python(self):
        # build a form, add two elements with communication rules.
        # make sure that the elements with communication rules communicate as
        # expected.
        new_element_A = elements.Element({
            'id': 'element_A',
            'type': 'folder',
            'validateAs': {'type': 'folder'},
            'args_id': 'temp_dir',
            'default_value': '/tmp',
            'signals': [
                {
                    'signal_name': 'visibility_changed',
                    'target': 'Element:workspace.set_enabled',
                },
            ]
        })

        # Verify that the target signal is not already in the affected
        # communicator.
        target_func = self.form.elements[0].set_enabled
        affected_communicator = new_element_A.visibility_changed
        self.assertFalse(target_func in affected_communicator.callbacks)

        self.form.add_element(new_element_A)

        # verify that the visibility_changed communicator has the function at
        # workspace.set_enabled in its registry.
        self.assertTrue(target_func in affected_communicator.callbacks)

        # now, assert that the visibility_changed communicator properly changes
        # the target_element.
        workspace_element = self.form.elements[0]
        self.assertTrue(workspace_element.is_visible())
        new_element_A.set_visible(False)

        self.assertFalse(workspace_element.is_enabled())

        # And if we switch the visibility back, verify the switch went through.
        new_element_A.set_visible(True)
        self.assertTrue(workspace_element.is_enabled())

    def test_python_callback(self):
        def test_closure(a):
            print a
            test_closure.touched = True
        test_closure.touched = False  # initialize to False

        new_element_A = elements.File({
            'id': 'element_A',
            'type': 'folder',
            'validateAs': {'type': 'folder'},
            'args_id': 'temp_dir',
            'default_value': '/tmp',
            'signals': [
                {
                    'signal_name': 'validation_completed',
                    'target': test_closure,
                },
            ]
        })
        affected_communicator = new_element_A.validation_completed
        self.assertFalse(test_closure in affected_communicator.callbacks)
        self.assertFalse(test_closure.touched)

        self.form.add_element(new_element_A)

        self.assertTrue(test_closure in affected_communicator.callbacks)
        self.assertFalse(test_closure.touched)  # should not have been called yet

        new_element_A.validate()
        new_element_A._validator.join()
        self.assertTrue(test_closure.touched)

    def test_enabledby(self):
        # Verify that IUI-style enabledBy works.
        form_config = {
            "modelName": "Example form",
            "targetScript": os.path.join(TEST_DIR, 'data',
                'sample_scripts.py'),
            "elements": [
                {
                    "id": "checkbox_1",
                    "type": "checkbox",
                    "defaultValue": False,
                    "signals": ["enables:checkbox_2"]
                },
                {
                    "id": "checkbox_2",
                    "type": "checkbox",
                    "defaultValue": False,
                    "enabled": False,
                },
            ]
        }
        form = elements.Form(form_config)
        checkbox_1 = form.elements[0]
        checkbox_2 = form.elements[1]

        # Verify that checkbox 1 is enabled by default, but checkbox 2 is not
        self.assertTrue(checkbox_1.is_enabled())
        self.assertFalse(checkbox_2.is_enabled())

        # Check checkbox 1, and verify that checkbox 2 is enabled.
        checkbox_1.set_value(True)
        checkbox_1._validator.join()  # wait for the validator to finish.
        self.assertTrue(checkbox_2.is_enabled())

        # now, uncheck checkbox_1 and ensure that checkbox_2 is disabled
        checkbox_1.set_value(False)
        checkbox_1._validator.join()
        self.assertFalse(checkbox_2.is_enabled())

        # check it back, just for fun
        # Check checkbox 1, and verify that checkbox 2 is enabled.
        checkbox_1.set_value(True)
        checkbox_1._validator.join()  # wait for the validator to finish.
        self.assertTrue(checkbox_2.is_enabled())

        # check it yet again, for even more fun
        checkbox_1.set_value(False)
        checkbox_1._validator.join()
        self.assertFalse(checkbox_2.is_enabled())

        # if I set the value to its current state, there should be no change.
        checkbox_1.set_value(checkbox_1.value())
        checkbox_1._validator.join()
        self.assertFalse(checkbox_2.is_enabled())


    def test_enabledby_cascading(self):
        # Verify that IUI-style enabledBy works as exepcted AND that this can
        # cascade through multiple elements.
        form_config = {
            "modelName": "Example form",
            "targetScript": os.path.join(TEST_DIR, 'data',
                'sample_scripts.py'),
            "elements": [
                {
                    "id": "checkbox_1",
                    "type": "checkbox",
                    "defaultValue": False,
                    "signals": ["enables:checkbox_2"]
                },
                {
                    "id": "checkbox_2",
                    "type": "checkbox",
                    "defaultValue": False,
                    "enabled": False,
                    "signals": ["enables:checkbox_3"]
                },
                {
                    "id": "checkbox_3",
                    "type": "checkbox",
                    "defaultValue": False,
                    "enabled": False,
                },
            ]
        }
        form = elements.Form(form_config)
        checkbox_1 = form.elements[0]
        checkbox_2 = form.elements[1]
        checkbox_3 = form.elements[2]

        # Verify that checkbox 1 is enabled by default, but checkbox 2 is not
        self.assertTrue(checkbox_1.is_enabled())
        self.assertFalse(checkbox_2.is_enabled())
        self.assertFalse(checkbox_3.is_enabled())

        # Check checkbox_1, verify that checkbox_2 has been enabled.
        checkbox_1.set_value(True)
        checkbox_1._validator.join()
        self.assertTrue(checkbox_1.is_enabled())
        self.assertTrue(checkbox_2.is_enabled())
        self.assertFalse(checkbox_3.is_enabled())

        # now, check the second checkbox and verify that the 3rd has been
        # enabled
        checkbox_2.set_value(True)
        checkbox_2._validator.join()
        self.assertTrue(checkbox_1.is_enabled())
        self.assertTrue(checkbox_2.is_enabled())
        self.assertTrue(checkbox_3.is_enabled())

        # disable the first checkbox and checkboxes 2, 3 should be disabled.
        print 'test 3'
        checkbox_1.set_value(False)
        checkbox_1._validator.join()
        checkbox_2._validator.join()
        self.assertTrue(checkbox_1.is_enabled())
        self.assertFalse(checkbox_2.is_enabled())
        self.assertFalse(checkbox_3.is_enabled())


    def test_disabledby(self):
        # Verify that IUI-style disabledBy works.
        form_config = {
            "modelName": "Example form",
            "targetScript": os.path.join(TEST_DIR, 'data',
                'sample_scripts.py'),
            "elements": [
                {
                    "id": "checkbox_1",
                    "type": "checkbox",
                    "defaultValue": False,
                    "signals": ["disables:checkbox_2"]
                },
                {
                    "id": "checkbox_2",
                    "type": "checkbox",
                    "defaultValue": False,
                    "enabled": True,
                },
            ]
        }
        form = elements.Form(form_config)
        checkbox_1 = form.elements[0]
        checkbox_2 = form.elements[1]

        # Verify that checkboxes 1, 2 is enabled by default
        self.assertTrue(checkbox_1.is_enabled())
        self.assertTrue(checkbox_2.is_enabled())

        # Check checkbox 1, and verify that checkbox 2 is disabled.
        checkbox_1.set_value(True)
        checkbox_1._validator.join()  # wait for the validator to finish.
        self.assertFalse(checkbox_2.is_enabled())

        # now, uncheck checkbox_1 and ensure that checkbox_2 is enabled
        checkbox_1.set_value(False)
        checkbox_1._validator.join()
        self.assertTrue(checkbox_2.is_enabled())

        # check it back, just for fun
        # Check checkbox 1, and verify that checkbox 2 is disabled.
        checkbox_1.set_value(True)
        checkbox_1._validator.join()  # wait for the validator to finish.
        self.assertFalse(checkbox_2.is_enabled())

        # check it yet again, for even more fun
        checkbox_1.set_value(False)
        checkbox_1._validator.join()
        self.assertTrue(checkbox_2.is_enabled())

        # if I set the value to its current state, there should be no change.
        checkbox_1.set_value(checkbox_1.value())
        checkbox_1._validator.join()
        self.assertTrue(checkbox_2.is_enabled())

    def test_disabledby_cascading(self):
        # Verify that IUI-style disabledBy works AND that this can cascade
        # through multiple elements.
        form_config = {
            "modelName": "Example form",
            "targetScript": os.path.join(TEST_DIR, 'data',
                'sample_scripts.py'),
            "elements": [
                {
                    "id": "checkbox_1",
                    "type": "checkbox",
                    "defaultValue": False,
                    "signals": ["disables:checkbox_2"]
                },
                {
                    "id": "checkbox_2",
                    "type": "checkbox",
                    "defaultValue": False,
                    "signals": ["disables:checkbox_3"],
                    "enabled": True,
                },
                {
                    "id": "checkbox_3",
                    "type": "checkbox",
                    "defaultValue": False,
                    "enabled": True,
                },
            ]
        }
        form = elements.Form(form_config)
        checkbox_1 = form.elements[0]
        checkbox_2 = form.elements[1]
        checkbox_3 = form.elements[2]

        # Verify that checkboxes 1, 2, 3 are enabled by default
        self.assertTrue(checkbox_1.is_enabled())
        self.assertTrue(checkbox_2.is_enabled())
        self.assertTrue(checkbox_3.is_enabled())

        self.assertFalse(checkbox_1.value())  # unchecked by default
        self.assertFalse(checkbox_2.value())  # unchecked by default
        self.assertFalse(checkbox_3.value())  # unchecked by default

        # For this test, all checkboxes start out enabled and unchecked
        # Check checkbox 2, and checkbox 3 should disable.
        # Check checkbox 1 and checkbox 2 should disable.
        checkbox_2.set_value(True)
        checkbox_2._validator.join()
        self.assertTrue(checkbox_2.value())
        self.assertTrue(checkbox_2.is_enabled())
        self.assertFalse(checkbox_3.is_enabled())

        checkbox_1.set_value(True)
        checkbox_1._validator.join()
        checkbox_2._validator.join()
        self.assertTrue(checkbox_1.value())
        self.assertTrue(checkbox_2.value())  # value should still be True
        self.assertFalse(checkbox_2.is_enabled())
        self.assertFalse(checkbox_2.is_enabled())

        # now, unchecking checkbox_1 should enable both checkbox 2, but leave
        # checkbox 3 disabled.
        checkbox_1.set_value(False)
        checkbox_1._validator.join()
        checkbox_2._validator.join()
        self.assertFalse(checkbox_1.value())
        self.assertTrue(checkbox_2.value())
        self.assertTrue(checkbox_2.is_enabled())
        self.assertFalse(checkbox_3.is_enabled())

    def test_element_index(self):
        expected_element_index = [
            'cbc4d60d477c32883a589588fdfd4ac9',
            'file_1',
            'file_2',
            'text_1',
            'workspace',
        ]

        self.assertEqual(sorted(self.form.element_index),
            expected_element_index)
        self.assertEqual(len(self.form.element_index), 5)

        # If I add an element, I need to see that element in the element index.
        new_element = elements.File({
            "label": "hello",
            "type": "file",
            "defaultValue": "something",
        })
        self.form.add_element(new_element)
        self.assertEqual(len(self.form.element_index), 6)
        self.assertTrue(new_element.get_id('user') in self.form.element_index)

    def test_expostfacto_signals(self):
        form_config = {
            "modelName": "Example form",
            "targetScript": os.path.join(TEST_DIR, 'data',
                'sample_scripts.py'),
            "elements": [
                {
                    "id": "checkbox_1",
                    "type": "checkbox",
                    "defaultValue": False,
                    "signals": ["disables:checkbox_2"]
                },
                {
                    "id": "checkbox_2",
                    "type": "checkbox",
                    "defaultValue": False,
                    "signals": ["disables:checkbox_3"],
                    "enabled": True,
                },
            ]
        }
        form = elements.Form(form_config)

        # now that the form has been set up, checkbox_2 has a signal that
        # could not evaluate, so it should be in the form._unknown_signals set.
        # Verify that this is the case.
        self.assertEqual(len(form._unknown_signals), 1)



        checkbox_3 = elements.CheckBox({
            "id": "checkbox_3",
            "type": "checkbox",
            "defaultValue": False,
            "enabled": True,
        })
        # before we add the checkbox, assert that there aren't any connections
        # in the checkbox_3 satisfaction_changed signal callbacks list.
        self.assertEqual(len(checkbox_3.satisfaction_changed.callbacks), 0)

        form.add_element(checkbox_3)
        self.assertEqual(len(form._unknown_signals), 0)
        self.assertEqual(len(form.elements[1].satisfaction_changed.callbacks), 1)
        self.assertTrue(checkbox_3.set_disabled in
            form.elements[1].satisfaction_changed.callbacks)

    def test_conditional_requirements(self):
        # Build a Form instance with all of the needed elements to test
        # conditional requirements.
        # Assert that conditional requirements are initialized correctly
        # Assert that conditional requirements change as expected when
        # satsifaction changes.
        form = elements.Form({
            'modelName': 'Example',
            "targetScript": os.path.join(TEST_DIR, 'data',
                'sample_scripts.py'),
            "elements": [
                {
                    "id": "text_1",
                    "type": "text",
                    "defaultValue": False,
                    "signals": ["set_required:text_2"]
                },
                {
                    "id": "text_2",
                    "type": "text",
                    "defaultValue": "",
                    "required": False
                },
            ]
        })
        text_1 = form.elements[0]
        text_2 = form.elements[1]
        self.assertFalse(text_1.is_required())
        self.assertFalse(text_2.is_required())

        # set the first text field so that it is satisfied.  When it is
        # satisfied, it should trigger the set_required signal, causing text_2
        # to be required.
        self.assertFalse(text_1.is_required())
        self.assertFalse(text_2.is_required())
        text_1.set_value('aaa')
        text_1._validator.join()
        self.assertTrue(text_1.is_satisfied())
        self.assertFalse(text_1.is_required())
        self.assertTrue(text_2.is_required())

    def test_conditional_requirements_initial(self):
        # verify that if satisfaction is initialized to a particular state, the
        # triggered elements should react appropriately
        form = elements.Form({
            'modelName': 'Example',
            "targetScript": os.path.join(TEST_DIR, 'data',
                'sample_scripts.py'),
            "elements": [
                {
                    "id": "text_1",
                    "type": "text",
                    "defaultValue": 'aaa',
                    "signals": ["set_required:text_2"]
                },
                {
                    "id": "text_2",
                    "type": "text",
                    "defaultValue": "",
                    "required": False
                },
            ]
        })
        text_1 = form.elements[0]
        text_2 = form.elements[1]
        text_1._validator.join()  # join in case validation not done.
        text_2._validator.join()

        # verify initial required/satisfied states.
        self.assertFalse(text_1.is_required())
        self.assertTrue(text_1.is_satisfied())  # has input, is valid
        self.assertTrue(text_2.is_required())  # b/c text_1 is satisfied

        # set the value of text_1 again and verify that the same satisfaction
        # and requirement is retained.
        text_1.set_value('bbb')
        text_1._validator.join()
        self.assertFalse(text_1.is_required())
        self.assertTrue(text_1.is_satisfied())
        self.assertTrue(text_2.is_required())

        # now, set the text_1 value to "".  Text_1 won't be satisfied so it
        # should trigger text_2 to no longer be required.
        text_1.set_value('')
        text_1._validator.join()
        self.assertFalse(text_1.is_required())
        self.assertFalse(text_1.is_satisfied())  # no longer satisfied
        self.assertFalse(text_2.is_required())  # b/c text_1 not satisfied.

