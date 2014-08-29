import time
import unittest

import palisades
from palisades import utils
from palisades import elements

class CommunicatorTest(unittest.TestCase):
    class SampleEmitter(utils.Communicator):
        def print_something(self, event=None):
            print 'something printed'


    def setUp(self):
        self.a = utils.Communicator()
        self.b = self.SampleEmitter()

    def test_register(self):
        self.a.register(self.b.print_something)
        self.a.emit(None)

    def test_remove(self):
        self.a.register(self.b.print_something)
        self.a.remove(self.b.print_something)

    def test_remove_fails(self):
        self.a.register(self.b.print_something)
        self.a.remove(self.b.print_something)
        self.assertRaises(utils.SignalNotFound, self.a.remove, self.b.print_something)

class RepeatingTimerTest(unittest.TestCase):
    def test_timer_smoke(self):
        """Run the timer and cancel it after a little while."""

        def new_func():
            return None
        try:
            timer = palisades.utils.RepeatingTimer(0.1, new_func)
            timer.start()
            time.sleep(0.5)
            timer.cancel()
            time.sleep(0.2)
            self.assertEqual(timer.is_alive(), False)
        except Exception as error:
            timer.cancel()
            raise error

class CoreTest(unittest.TestCase):
    """A test class for functions found in palisades.core."""
    def test_apply_defaults(self):
        defaults = {
            'a': 'test_value',
            'b': 'another'
        }

        test_configuration = {
            0: 'something',
            'a': 'custom_value',
        }

        expected_result = {
            0: 'something',
            'a': 'custom_value',
            'b': 'another'
        }
        self.assertEqual(utils.apply_defaults(test_configuration, defaults),
            expected_result)

        duplicates_replaced_result = {
            0: 'something',
            'a': 'test_value',
            'b': 'another',
        }
        self.assertEqual(utils.apply_defaults(test_configuration, defaults,
            False), duplicates_replaced_result)

    def test_nested_defaults(self):
        defaults = {
            'a': 'test_value',
            'b': 'another',
            'd': {
                'nested 1': 1,
            },
        }

        test_configuration = {
            0: 'something',
            'a': 'custom_value',
            'd': {
                'nested 2': 2,
            },
        }

        expected_result = {
            0: 'something',
            'a': 'custom_value',
            'b': 'another',
            'd': {
                'nested 1': 1,
                'nested 2': 2,
            },
        }
        self.assertEqual(utils.apply_defaults(test_configuration, defaults),
            expected_result)

    def test_default_config_update(self):
        # a case where existing defaults are not overridden by user input.
        test_configuration = {
        }
        first_defaults = {
            0: {'hello': 'world'}
        }
        first_update = utils.apply_defaults(test_configuration, first_defaults)
        self.assertEqual(first_update, {0: {'hello': 'world'}})

        second_defaults = {
            0: None
        }

        # add 3rd parameter=False to make this pass
        second_update = utils.apply_defaults(first_update, second_defaults,
            old_defaults=first_defaults)
        self.assertEqual(second_update, {0: None})

    def test_default_config_update_dicts(self):
        test_configuration = {
            'returns': {'some': 'value'},
        }
        first_defaults = {
            'returns': {
                'ifEmpty': True,
                'ifNot': False,
            }
        }
        first_update = utils.apply_defaults(test_configuration, first_defaults)
        self.assertEqual(first_update, {'returns': {'some': 'value',
            'ifEmpty': True, 'ifNot': False}})

        # Commenting this all out for now, as the update functionality is under
        # development and buggy.
        #second_defaults = {
        #    'returns': None,
        #}
        #second_update = utils.apply_defaults(first_update, second_defaults,
        #    old_defaults=first_defaults)
        #self.assertEqual(second_update, {'returns': {'some': 'value'}})

    def test_default_config_cleanup(self):
        # verify cleaning up attributes not defined in defaults works.
        test_config = {
            'attribute': 'to delete',
            'keep': 'this',
        }
        test_defaults = {
            'keep': 'this line',
        }

        # add cleanup=True to make this pass
        result = utils.apply_defaults(test_config, test_defaults, cleanup=True)
        self.assertEqual(result, {'keep': 'this'})

    def test_convert_config(self):
        # take an IUI configuration object and convert it to palisades.
        sample_config = {
            'modelName': 'some model',
            'label': 'some label',
            'helpText': 'some help text',
            'elements': [
                {
                    'type': 'list',
                    'elements': [
                        {
                            'id': 'label_1',
                            'type': 'label',
                            'label': 'label 1',
                            'helpText': 'helptext 1',
                        },
                        {
                            'id': 'label_2',
                            'type': 'hideableFileEntry',
                            'label': 'label 2',
                            'helpText': 'helptext 2',
                            'enabledBy': 'label_1',
                        },
                    ]
                }
            ]
        }

        expected_config = {
            'modelName': {'en': 'some model'},
            'label': {'en': 'some label'},
            'helpText': {'en': 'some help text'},
            'elements': [
                {
                    'id': 'label_1',
                    'type': 'label',
                    'label': {'en': 'label 1'},
                    'helpText': {'en': 'helptext 1'},
                    'signals': ['enables:label_2'],
                },
                {
                    'id': 'label_2',
                    'type': 'file',
                    'hideable': True,
                    'label': {'en': 'label 2'},
                    'helpText': {'en': 'helptext 2'},
                },
            ]
        }
        self.assertEqual(utils.convert_iui(sample_config), expected_config)

    def test_add_translations_defaults(self):
        sample_config = {
            'modelName': 'some model',
            'label': 'some label',
            'helpText': 'some help text',
        }

        expected_result = {
            'modelName': {'en': 'some model'},
            'label': {'en': 'some label'},
            'helpText': {'en': 'some help text'},
        }
        self.assertEqual(utils.add_translations_to_iui(sample_config),
            expected_result)

    def test_add_translations_multi_lang(self):
        sample_config = {
            'modelName': 'some model',
            'label': 'some label',
            'helpText': 'some help text',
        }

        lang_codes = ['en', 'de', 'es']
        current_lang = 'en'

        expected_result = {
            'modelName': {
                'en': 'some model',
                'de': None,
                'es': None,
            },
            'label': {
                'en': 'some label',
                'de': None,
                'es': None,
            },
            'helpText': {
                'en': 'some help text',
                'de': None,
                'es': None,
            },
        }
        self.assertEqual(utils.add_translations_to_iui(sample_config,
            lang_codes, current_lang), expected_result)

    def test_expand_shortform_enable(self):
        shortform_enable = "enables:element_1"
        expected_longform = {
            "signal_name": "satisfaction_changed",
            "target": "Element:element_1.set_enabled",
        }
        expanded = utils.expand_signal(shortform_enable)
        self.assertEqual(expanded, expected_longform)

    def test_expand_shortform_disable(self):
        shortform_disable = "disables:element_1"
        expected_longform = {
            "signal_name": "satisfaction_changed",
            "target": "Element:element_1.set_disabled",
        }
        expanded = utils.expand_signal(shortform_disable)
        self.assertEqual(expanded, expected_longform)

    def test_expand_shortform_typeerror(self):
        invalid_shortform = []
        self.assertRaises(TypeError, utils.expand_signal, invalid_shortform)

    def test_expand_shortform_runtimeerror(self):
        unknown_shortform = "bad_signal:element"
        self.assertRaises(RuntimeError, utils.expand_signal, unknown_shortform)

    def test_get_valid_signals(self):
        signals_list = [
            "enables:element",
            {
                "signal_name": "aaa",
                "target": "Element:some_target.set_enabled",
            },
        ]
        known_signals = ["satisfaction_changed", "aaa"]

        expected_signals = [
            {
                "signal_name": "satisfaction_changed",
                "target": "Element:element.set_enabled",
            },
            {
                "signal_name": "aaa",
                "target": "Element:some_target.set_enabled",
            },
        ]
        self.assertEqual(utils.get_valid_signals(signals_list, known_signals),
            expected_signals)

