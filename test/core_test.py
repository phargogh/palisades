import unittest

from palisades import core
from palisades import elements

class CommunicatorTest(unittest.TestCase):
    class SampleEmitter(core.Communicator):
        def print_something(self, event=None):
            print 'something printed'


    def setUp(self):
        self.a = core.Communicator()
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
        self.assertRaises(core.SignalNotFound, self.a.remove, self.b.print_something)

class ElementTest(unittest.TestCase):
    class Incrementer(object):
        counter = 0
        def increment(self):
            self.counter += 1

    def setUp(self):
        self.counter = self.Incrementer()
        self.element = elements.Primitive({})

    def test_set_value(self):
        self.element.register(self.counter.increment)
        self.element.set_value('aaa') # increment
        self.assertEqual(self.counter.counter, 1)

        self.element.set_value('aaa')  # no increment
        self.assertEqual(self.counter.counter, 1)

        self.element.set_value('b')  # increment
        self.assertEqual(self.counter.counter, 2)

    def test_is_enabled(self):
        self.assertEqual(self.element.is_enabled(), True)
        self.element.disable()
        self.assertEqual(self.element.is_enabled(), False)
        self.element.enable()
        self.assertEqual(self.element.is_enabled(), True)

    def test_set_value_when_disabled(self):
        self.assertEqual(self.element.is_enabled(), True)
        self.element.set_value('aaa')
        self.assertEqual(self.element.value(), 'aaa')
        self.element.disable()
        self.element.set_value('bbb')
        self.assertEqual(self.element.value(), 'aaa')


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
        self.assertEqual(core.apply_defaults(test_configuration, defaults),
            expected_result)

        duplicates_replaced_result = {
            0: 'something',
            'a': 'test_value',
            'b': 'another',
        }
        self.assertEqual(core.apply_defaults(test_configuration, defaults,
            False), duplicates_replaced_result)

class FileTest(unittest.TestCase):
    def setUp(self):
        self.element = core.File()

    def test_set_value_utf8(self):
        # verify that if we set the value with a unicode string,
        # we get a unicode string out
        self.element.set_value(u'aaa')
        returned_string = self.element.get_value()
        self.assertEqual(type(returned_string), unicode)

    def test_set_value_ascii(self):
        #Verify that if we set the value with an ascii string,
        # we get a unicode string out
        self.element.set_value('aaa')
        returned_string = self.element.get_value()
        self.assertEqual(type(returned_string), unicode)

