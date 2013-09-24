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

