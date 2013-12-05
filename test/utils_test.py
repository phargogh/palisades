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
                            'type': 'label',
                            'label': 'label 1',
                            'helpText': 'helptext 1'
                        },
                        {
                            'type': 'hideableFileEntry',
                            'label': 'label 2',
                            'helpText': 'helptext 2',
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
                    'type': 'label',
                    'label': {'en': 'label 1'},
                    'helpText': {'en': 'helptext 1'}
                },
                {
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

