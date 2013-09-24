import unittest
import os

from palisades import elements

TEST_DIR = os.path.dirname(__file__)
IUI_CONFIG = os.path.join(TEST_DIR, 'data', 'iui_config')


class ApplicationTest(unittest.TestCase):
    def test_build_application(self):
        elements.Application(os.path.join(IUI_CONFIG,
            'timber.json'))
