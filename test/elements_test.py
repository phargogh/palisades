import unittest
import os

from palisades import elements

TEST_DIR = os.path.dirname(__file__)
IUI_CONFIG = os.path.join(TEST_DIR, 'data', 'iui_config')
PALISADES_CONFIG = os.path.join(TEST_DIR, 'data', 'palisades_config')

class ApplicationTest(unittest.TestCase):
    def test_build_application(self):
        ui = elements.Application(os.path.join(PALISADES_CONFIG,
            'timber_clean.json'))
        ui.run()
