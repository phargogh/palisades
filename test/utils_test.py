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

