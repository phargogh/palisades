import time
import unittest
import os.path

import palisades
from palisades import utils
from palisades import elements

import mock


def some_function():
    pass

class CommunicatorTest(unittest.TestCase):

    def setUp(self):
        self.a = utils.Communicator()
        #self.b = self.SampleEmitter()

    def test_register(self):
        from palisades import utils
        a = utils.Communicator()

        def mock_func(*args, **kwargs):
            print 'yep, called it!'
            mock_func.called = True
        mock_func.called = False
        self.mock_func = mock_func

        #mock_func = PickleableMock()
        #mock_func = mock.mock.Mock()
        #mock_func = mock.MagicMock()
        with mock.patch('os.path.join') as mocked_func:
            a.register(mocked_func)
            a.emit(None, join=True)
            print mocked_func
            print mocked_func.__dict__

            self.assertTrue(os.path.join.called)

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


class DefaultsTest(unittest.TestCase):
    def test_apply_single_level_defaults_all_values_exist(self):
        defaults = {
            'a': 1,
            'b': 2,
        }

        user_config = {
            'a': 'a',
            'b': 2,
        }

        merged_config = utils.apply_defaults(user_config, defaults)
        self.assertEqual(
            merged_config,
            {
                'a': 'a',
                'b': 2
            }
        )

    def test_apply_single_level_defaults_missing_values(self):
        defaults = {
            'a': 1,
            'b': 2,
            'c': 3
        }
        user_config = {}
        merged_config = utils.apply_defaults(user_config, defaults)
        self.assertEqual(merged_config, defaults)

    def test_apply_nested_defaults_all_values_exist(self):
        defaults = {
            'a': 1,
            'b': 2,
            'c': {
                'd': 4,
                'e': 5,
            }
        }
        user_config = {
            'a': 'a',
            'b': 2,
            'c': {
                'd': 'd',
                'e': 'e',
            }
        }
        merged_config = utils.apply_defaults(user_config, defaults)
        self.assertEqual(merged_config, user_config)

    def test_apply_nested_defaults_missing_values(self):
        defaults = {
            'a': 1,
            'b': 2,
            'c': {
                'd': 4,
                'e': 5,
            }
        }
        user_config = {
            'a': 'a'
        }
        merged_config = utils.apply_defaults(user_config, defaults)
        self.assertEqual(
            merged_config,
            {
                'a': 'a',
                'b': 2,
                'c': {
                    'd': 4,
                    'e': 5,
                }
            })

    def test_apply_flat_defaults_type_mismatch(self):
        defaults = {
            'a': 1
        }
        user_config = {
            'a': ['foo']
        }

        merged_config = utils.apply_defaults(user_config, defaults)
        self.assertEqual(merged_config, user_config)

    def test_apply_nested_defaults_type_mismatch(self):
        defaults = {
            'a': 1,
            'b': {
                'c': [1],
            }
        }
        user_config = {
            'a': 'a',
            'b': {
                'c': 1,
            }
        }

        merged_config = utils.apply_defaults(user_config, defaults)
        self.assertEqual(merged_config, user_config)

    def test_apply_nested_defaults_user_defined_no_default(self):
        defaults = {
            'a': 1,
        }
        user_config = {
            'b': 2
        }
        merged_config = utils.apply_defaults(user_config, defaults)
        self.assertEqual(
            merged_config,
            {
                'a': 1,
                'b': 2,
            }
        )



class CoreTest(unittest.TestCase):
    """A test class for functions found in palisades.core."""

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

    def test_convert_config_map_values_dict(self):
        # Convert an IUI dict that includes a mapValues element that is a dict.

        iui_config = {
            "type": "dropdown",
            "args_id": "dropdown_args_id",
            "label": "foo",
            "options": ["Square", "Hexagon"],
            "defaultValue": "Hexagon",
            "required": True,
            "returns": {
                "mapValues": {
                    "Square": "square",
                    "Hexagon": "hexagon"
                }
            }
        }

        expected_config = {
            'type': 'dropdown',
            'args_id': 'dropdown_args_id',
            'defaultValue': 'Hexagon',
            'label': {'en': 'foo'},
            'options': {'en': ['Square', 'Hexagon']},
            'required': True,
            'returns': {
                'mapValues': {
                    'Hexagon': 'hexagon',
                    'Square': 'square'
                },
                'type': 'string'},
        }

        self.assertEqual(utils.convert_iui(iui_config), expected_config)

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
                            'requiredIf': ['label_2', 'label_3'],
                        },
                        {
                            'id': 'label_2',
                            'type': 'hideableFileEntry',
                            'label': 'label 2',
                            'helpText': 'helptext 2',
                            'enabledBy': 'label_1',
                        },
                        {
                            'id': 'label_3',
                            'type': 'hideableFileEntry',
                            'label': 'label 3',
                            'helpText': 'helptext 3',
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
                    'signals': ['set_required:label_1'],
                },
                {
                    'id': 'label_3',
                    'type': 'file',
                    'hideable': True,
                    'label': {'en': 'label 3'},
                    'helpText': {'en': 'helptext 3'},
                    'signals': ['set_required:label_1'],
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

