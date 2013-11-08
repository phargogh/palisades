import unittest

import mock
from PyQt4.QtTest import QTest

from palisades.gui import qt4

APPLICATION = qt4.Application()

class QtWidgetTest(unittest.TestCase):
    def setUp(self):
        self.widget = qt4.QtWidget()

    def test_visibility(self):
        # assert widget is visible by default (as long as the widget has been
        # shown).
        self.assertEqual(self.widget.isVisible(), False)
        self.widget.show()
        self.assertEqual(self.widget.isVisible(), True)

        # set widget visibility to False
        self.widget.set_visible(False)
        self.assertEqual(self.widget.isVisible(), False)

        # reset widget visibility and verify change.
        self.widget.set_visible(True)
        self.assertEqual(self.widget.isVisible(), True)
