import unittest
import os
import time
from types import ListType

import mock

from PyQt4.QtTest import QTest

from palisades import elements
from palisades.gui import core

# view for the GUI layer

APPLICATION = core.ApplicationGUI()

class UIObjectIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.element = elements.Element({})
        self.view = core.UIObject(self.element)

    def test_visibility(self):
        # verify that when the core element's visibility changes, this view's
        # set_visible function is called.
        # this happens because the core element's set_visible function causes
        # the visibility_changed signal to be emitted, which then causes the
        # palisades.gui.core.UIObject.set_visible() function to be called,
        # which currently just raises NotYetImplemented.
        self.assertRaises(core.NotYetImplemented, self.element.set_visible,
            not self.element.is_visible())

        self.assertRaises(core.NotYetImplemented, self.view.set_visible, True)

# TODO: add a test that verifies behavior on validation completion.
class PrimitiveIntegrationTest(UIObjectIntegrationTest):
    def setUp(self):
        self.element = elements.Primitive({})
        self.view = core.PrimitiveGUI(self.element)

    def test_visibility(self):
        # this is effectively a smoke test for this function, since there are no
        # widgets in the PrimitiveGUI view class.
        for widget in self.view.widgets:
            self.assertEqual(widget.is_visible(), False, ('Widget %s'
                ' is not visible when it should be') % widget)

        self.view.set_visible(True)
        for widget in self.view.widgets:
            self.assertEqual(widget.is_visible(), True)

        # verify that when the core element's visibility changes, this view's
        # set_visible function is called.
        is_visible = self.element.is_visible()
        self.element.visibility_changed.emit(not is_visible)
        for widget in self.view.widgets:
            self.assertEqual(widget.is_visible(), not is_visible)

class LabeledPrimitiveIntegrationTest(PrimitiveIntegrationTest):
    def setUp(self):
        self.element = elements.LabeledPrimitive({})
        self.view = core.LabeledPrimitiveGUI(self.element)

    def test_hideable(self):
        # assumes that hideability is off by default.
        # when the core element is hideable, we use a checkbox instead of the
        # label, which has some slightly different behavior.
        self.element._hideable = True  # make element hideable to verify behavior
        self.assertEqual(self.element.is_hideable(), True) # verify before tests

        # need to re-create the view for this test to work properly, since the
        # hideability checkbox is created on __init__.
        self.view = core.LabeledPrimitiveGUI(self.element)

        # TODO: Verify default widget visibility (issue 2470)

        # I need to show these widgets manually here to simulate the widgets
        # actually being visible to the user in a UI.
        for widget in self.view.widgets:
            widget.show()

        # when hideable, self.view._label is a checkbox that can be checked on
        # and off using the set_checked() function.  When the checkbox is
        # checked, verify that the other widgets are toggled correctly
        self.assertEqual(self.element.is_hidden(), False)
        self.assertEqual(self.view._label.is_checked(), True)

        self.assertEqual(self.view._label.is_visible(), True)
        self.view._label.set_checked(True)
        for widget in self.view.widgets:
            self.assertEqual(widget.is_visible(), True, ('Widget %s'
                ' is not visible when it should be') % widget)

        # when the hideable checkbox is unchecked, all non- view._label widgets
        # should be made invisible.
        self.view._label.set_checked(False)
        for widget in self.view.widgets:
            if widget is self.view._label:
                self.assertEqual(widget.is_visible(), True, ('Widget %s'
                ' is not visible when it should be') % widget)
            else:
                self.assertEqual(widget.is_visible(), False, ('Widget %s'
                ' is visible when it should not be') % widget)

    def test_set_value(self):
        # I want this test function to pass for this class, but fail hard for
        # all subclasses unless reimplemented there.  This is because the
        # set_value functionality is not specified in the LabeledPrimitiveGUI
        # class.
        # This function will be able to be the single point of entry when the
        # TODO in LabeledPrimitiveGUI.set_widget() is addressed.
        if self.__class__.__name__ == 'LabeledPrimitiveIntegrationTest':
            pass
        else:
            raise AssertionError('Not yet implemented!')

class CheckBoxIntegrationTest(LabeledPrimitiveIntegrationTest):
    def setUp(self):
        self.element = elements.CheckBox({})
        self.view = core.CheckBoxGUI(self.element)

    def test_set_value(self):
        # check the current value of the element and the check state of the
        # checkbox before we begin this series of tests.
        self.assertEqual(self.element.value(), False)
        self.assertEqual(self.view._checkbox.is_checked(), False)

        # verify that when the checkbox is checked, the core element gets the
        # message.
        self.view._checkbox.set_checked(True)
        self.assertEqual(self.element.value(), True)

        # verify that when the checkbox is unchecked, the core element once
        # again gets the message.
        self.view._checkbox.set_checked(False)
        self.assertEqual(self.element.value(), False)

class TextIntegrationTest(LabeledPrimitiveIntegrationTest):
    def setUp(self):
        self.element = elements.Text({})
        self.view = core.TextGUI(self.element)
        self.sample_value = 'hello world!'

    def test_set_value(self):
        # check the current value of the element and the textfield widget before
        # we begin this series of tests.
        self.assertEqual(self.element.value(), '')
        self.assertEqual(self.view._text_field.text(), '')

        # verify that when the textfield's text is set, the core element gets
        # the message and updates its value.
        self.view._text_field.set_text(self.sample_value)
        QTest.qWait(50)  # wait for the qt event loop to detect change.
        self.assertEqual(self.view._text_field.text(), self.sample_value)
        self.assertEqual(self.element.value(), self.sample_value)

class FileIntegrationTest(TextIntegrationTest):
    def setUp(self):
        self.element = elements.File({'type': 'file'})
        self.view = core.FileGUI(self.element)
        self.sample_value = __file__

    def test_file_selected(self):
        # check the current value of the element and the textfield widget before
        # we begin the series of tests.
        self.assertEqual(self.element.value(), '')
        self.assertEqual(self.view._text_field.text(), '')

        # verify that when the file button's file_selected signal is emitted,
        # the textfield's text is updated and the core element is notified.
        self.view._file_button.file_selected.emit(self.sample_value)
        self.assertEqual(self.view._text_field.text(), self.sample_value)
        self.assertEqual(self.element.value(), self.sample_value)

class DropdownIntegrationTest(LabeledPrimitiveIntegrationTest):
    def setUp(self):
        self.element = elements.Dropdown({'options': ['a', 'b', 'c']})
        self.view = core.DropdownGUI(self.element)

    def test_set_value(self):
        # check the current value of the element and the index of the
        # dropdown before we begin this series of tests.
        self.assertEqual(self.element.value(), 'a')
        self.assertEqual(self.view._dropdown.index(), 0)

        # verify that when the dropdown's selection changes, the core element is
        # notified.
        self.view._dropdown.set_index(1)
        self.assertEqual(self.element.value(), 'b')

class GroupIntegrationTest(UIObjectIntegrationTest):
    def setUp(self):
        self.contained_elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]
        self.config = {'elements': self.contained_elements}
        self.element = elements.Group(self.config)
        self.view = core.GroupGUI(self.element)

    # TODO: Do I need to reimplement test_visibility?

    def test_contained_elements(self):
        # verify that the correct elements are created.
        expected_elements = [
            (0, core.FileGUI),
            (1, core.TextGUI),
        ]
        for index, classname in expected_elements:
            is_instance = isinstance(self.view.elements[index], classname)
            self.assertEqual(is_instance, True)

class ContainerIntegrationTest(GroupIntegrationTest):
    def setUp(self):
        self.contained_elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]
        self.config = {'elements': self.contained_elements}
        self.element = elements.Container(self.config)
        self.view = core.ContainerGUI(self.element)

    def test_collapsibility(self):
        # The default collapsibility is False, so I'll verify here that the
        # toolkit's collapsibility matches the element's collapsibility.
        self.assertEqual(self.element.is_collapsible(), False)
        self.assertEqual(self.view.widgets.is_collapsible(), False)
        self.assertRaises(RuntimeError, self.view.widgets.set_collapsed, True)

        # to test collapsibility, I need to create a container that is
        # collapsible.
        config = self.config.copy()
        config.update({'collapsible': True})
        self.element = elements.Container(config)
        self.view = core.ContainerGUI(self.element)

        # verify that the newly created element is collapsible, as is the view,
        # but that the container is expanded by default.
        self.assertEqual(self.element.is_collapsible(), True)
        self.assertEqual(self.view.widgets.is_collapsible(), True)
        self.assertEqual(self.view.widgets.is_collapsed(), False)

        # now, simulate a user click on the collapsible container and verify
        # that both the element and the view are collapsed.
        self.view.widgets.set_collapsed(True)
        self.assertEqual(self.element.is_collapsed(), True)
        self.assertEqual(self.view.widgets.is_collapsed(), True)

        # now, set the state of the element to be uncollapsed and verify this
        # is reflected in the UI.
        self.element.set_state({'collapsed': False, 'enabled': True})
        self.assertFalse(self.element.is_collapsed())
        self.assertFalse(self.view.widgets.is_collapsed())

        self.element.set_state({'collapsed': True, 'enabled': True})
        self.assertTrue(self.element.is_collapsed())
        self.assertTrue(self.view.widgets.is_collapsed())

    def test_default_expanded(self):
        new_config = {'elements': self.contained_elements, 'collapsible': True,
            'defaultValue': False}
        element = elements.Container(new_config)
        view = core.ContainerGUI(element)

        # verify that the element and GUI both default to what's specified.
        self.assertFalse(element.is_collapsed())
        self.assertFalse(view.widgets.is_collapsed())
        self.assertTrue(element.is_collapsible())
        self.assertTrue(element.is_collapsible())

        def _check_interactivity(obj_list, expected):
            for contained_obj in obj_list:
                self.assertEqual(contained_obj.is_enabled(), expected)
                self.assertTrue(contained_obj.is_visible(), expected)

        # verify contained elements are enabled, since the contained is not
        # collapsed.
        _check_interactivity(element.elements(), True)

        # verify contained elements in the GUI are enabled, since the contained
        # is not collapsed.
        _check_interactivity(view.elements, True)

        # set the element state, have the change reflected in the GUI.
        element.set_state({'enabled': True, 'collapsed': True})
        _check_interactivity(element.elements(), False)
        _check_interactivity(view.elements, False)




class MultiIntegrationTest(ContainerIntegrationTest):
    def setUp(self):
        self.contained_elements = [
            {
                'type': 'file',
            },
            {
                'type': 'text',
            },
        ]
        self.config = {'elements': self.contained_elements}
        self.element = elements.Multi(self.config)
        self.view = core.MultiGUI(self.element)

    def test_contained_elements(self):
        # there should be no contained elements by default, even though there
        # are some contained elements in the user-defined config.
        self.assertEqual(len(self.view.elements), 0)

    def test_add_element(self):
        # verify that there are no elements ... yet
        self.assertEqual(self.view.widgets.count(), 0)
        self.assertEqual(len(self.element.elements()), 0)

        # click the add_another link.
        self.view.widgets.add_element_link.clicked.emit(True)

        # verify that a row has been added to the layout
        self.assertEqual(len(self.element.elements()), 1)
        self.assertEqual(self.view.widgets.count(), 1)

        # verify that there's a new element of the correct class in the core
        # element.  A Text element is created by default.
        self.assertEqual(self.element.elements()[0].__class__.__name__, 'Text')

    def test_remove_element(self):
        # simulate clicking the add another link to add three elements.
        self.view.widgets.add_element_link.clicked.emit(True)
        self.view.widgets.add_element_link.clicked.emit(True)
        self.view.widgets.add_element_link.clicked.emit(True)

        # to make it easier to test which element is which later on, I'll set
        # the values of the respective elements.
        self.element.elements()[0].set_value('aaa')
        self.element.elements()[1].set_value('bbb')
        self.element.elements()[2].set_value('ccc')

        # when the GUI's minus button is clicked, verify that the element in
        # core is removed and that the number of active elements in the Multi
        # widget is also correct.
        self.view.elements[0].widgets[0]._button_pushed()
#        print self.element.elements()
#        print [e.value() for e in self.element.elements()]
        self.assertEqual(len(self.element.elements()), 2)
        self.assertEqual(self.view.widgets.count(), 2)
        self.assertEqual(self.element.elements()[0].value(), 'bbb')
        self.assertEqual(self.element.elements()[1].value(), 'ccc')

#class TabGroupIntegrationTest(GroupIntegrationTest):

class LabelIntegrationTest(UIObjectIntegrationTest):
    def setUp(self):
        self.label = 'This is a label.'
        self.element = elements.Label({'label': self.label})
        self.view = core.LabelGUI(self.element)

    def test_contents(self):
        self.assertEqual(self.element.label(), self.label)
        self.assertEqual(self.view.widgets.text(), self.label)

    def test_visibility(self):
        # widget will not be visible until it's shown.
        self.assertEqual(self.view.widgets.is_visible(), False)
        self.view.widgets.show()
        self.assertEqual(self.view.widgets.is_visible(), True)
