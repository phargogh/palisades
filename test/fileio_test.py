import unittest
import os

from palisades import fileio

TEST_DIR = os.path.dirname(__file__)
FILEIO_DATA = os.path.join(TEST_DIR, 'data', 'fileio')

class ConfigTest(unittest.TestCase):
    def test_read_config(self):
        """Assert a simple json configuration can be read and accessed."""
        config_file = os.path.join(FILEIO_DATA, 'read_config.json')
        config_dict = fileio.read_config(config_file)
        self.assertEqual(config_dict['key'], "Test string")

    def test_config_malformed(self):
        """Assert that a malformed json file raises ValueError."""
        config_file = os.path.join(FILEIO_DATA, 'read_config_malformed.json')
        self.assertRaises(ValueError, fileio.read_config, config_file)

class PythonSavingTest(unittest.TestCase):
    def test_save_model_run(self):
        """Assert a model saves correctly."""
        test_dictionary = {
            'a': 1234,
            'b': 5.5,
            'c': [0, 1, 2, 3],
            'd': {'a': 'b'},
            u'e': 'aaaa',
            u'f': u'qwerty',
            1: 'hello',
            5.5: 'world'
        }
        output_file = os.path.join(FILEIO_DATA, 'test_model_save.py')
        module = 'hello.world'
        fileio.save_model_run(test_dictionary, module, output_file)

        regression_file = os.path.join(FILEIO_DATA, 'simple_model_save.py')
        lines = lambda f: [l for l in open(f)]
        for index, (out_msg, reg_msg) in enumerate(zip(lines(output_file),
            lines(regression_file))):

            # Skip the first couple lines which include date and version info
            # and may differ from run to run.
            if index > 0 and index <5:
                pass
            else:
                self.assertEqual(out_msg, reg_msg)
