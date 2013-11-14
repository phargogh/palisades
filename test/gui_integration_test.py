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
@unittest.skip('')
class QtTextIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'defaultValue': 'a',
        }
        self.element = elements.Text(config)
        self.gui = core.FileGUI(self.element)

    def test_text_changed(self):
        """Assert element's value when text field value is changed."""
        # assert that the starting value is what we set in the config.
        self.assertEqual(self.element.value(), 'a')

        new_value = 'hello world!'
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

        new_value = 'hello again!'
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

    def test_validation_completed(self):
        """Assert element's validation state when validation completes"""
        # assert that validation state is True by default.
        self.assertEqual(self.gui._validation_button.error_text , '')
        self.assertEqual(self.gui._validation_button.error_state, 'pass')
        self.assertEqual(self.gui._validation_button.isEnabled(), False)
        self.assertEqual(self.element.is_valid(), True)

        # verify that the validation thread has not yet been started
        self.assertEqual(self.element._validator.thread.is_alive(), False)

        # Trigger validation by setting the value of the text.
        self.gui._text_field.setText('new_value')

        # check that the validation thread has been started.
        self.assertRaises(RuntimeError, self.element._validator.thread.start)

        # check the validation state of the element
        self.assertEqual(self.element.is_valid(), True)

        # check the validation state of the GUI.
        self.assertEqual(self.gui._validation_button.error_state, 'pass')

@unittest.skip('')
class QtFileIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'defaultValue':  os.getcwd(),
            'validateAs': {
                'type': 'folder',
                'mustExist': True,
            }
        }
        self.element = elements.File(config)
        self.gui = core.FileGUI(self.element)

    def test_set_text(self):
        """Assert element's value when text field value is changed."""
        # assert that the starting value is what we set in the config.
        self.assertEqual(self.element.value(), os.getcwd())

        new_value = os.path.join(os.getcwd(), 'test')
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

        new_value = os.path.join(os.getcwd(), 'palisades')
        self.gui._text_field.setText(new_value)
        self.assertEqual(self.element.value(), new_value)

    def test_validation(self):
        """Assert that validation takes place when text is changed."""

        self.assertEqual(self.element.value(), os.getcwd())

        # check the validation state to start out
        self.assertEqual(self.gui._validation_button.error_state, 'pass')
        self.assertEqual(self.element.is_valid(), True)

        # set the textfield value to something else.
        new_value = os.path.join(os.getcwd(), 'test')
        self.element.set_value(new_value)
        self.assertEqual(self.element.value(), new_value)
        self.assertRaises(RuntimeError, self.element._validator.thread.start)
        QTest.qWait(100)
        self.assertEqual(self.element.is_valid(), True)

        # set the textfield value to something that we know will fail validation
        # Need to first verify that the folder that shouldn't exist doesn't.
        new_value = os.path.join(os.getcwd(), 'nonexistent_dir')
        self.assertEqual(os.path.exists(new_value), False)
        self.element.set_value(new_value)
        self.assertRaises(RuntimeError, self.element._validator.thread.start)

        # given the new value, verify that the element failed validation.
        QTest.qWait(100)
        self.assertEqual(self.element.is_valid(), False)

        # verify that the validation button displays the correct error state.
        self.assertEqual(self.gui._validation_button.error_state, 'error')
        self.assertEqual(self.gui._validation_button.isEnabled(), True)
        self.assertNotEqual(self.gui._validation_button.error_text, '')
        self.assertEqual(self.gui._validation_button.isFlat(), False)

    def test_file_button(self):
        """Assert that file selection sets the element value, starts validation"""
        self.assertEqual(self.element.value(), os.getcwd())

        # create a new path and emit the file_selected signal with it.
        # can't actually simulate the mousebutton click here or emit the Qt
        # signal because it will cause the program to present a Qt file dialog
        # and block the program on user input from the file window.
        new_path = os.path.join(os.getcwd(), 'test')
        self.gui._file_button.file_selected.emit(new_path)

        # verify that the new path has been set as the element value and is also
        # the value of the text field.
        QTest.qWait(100)
        self.assertEqual(str(self.gui._text_field.text()), new_path)
        self.assertEqual(self.element.value(), new_path)

@unittest.skip('')
class QtDropdownIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'label': 'A Dropdown',
            'options': ['a', 'b', 'c'],
            'defaultValue': 1,
            'returns': 'strings'
        }
        self.element = elements.Dropdown(config)
        self.gui = core.DropdownGUI(self.element)

    def test_setup(self):
        """Assert that the options in the dropdown are correct"""
        # build up a list of entries from the Qt widget.
        qt_options = [str(self.gui._dropdown.itemText(i)) for i in
            range(self.gui._dropdown.count())]

        # assert that the options in the Qt widget are the same as the options
        # specified in the dropdown.
        self.assertEqual(qt_options, ['a', 'b', 'c'])

        # assert the default index
        self.assertEqual(self.element.current_index(), 1, 'default index is not set')
        self.assertEqual(self.gui._dropdown.currentIndex(), 1)

    def test_select_option(self):
        """Assert behavior when user selects an option"""
        # assert the default index is set correctly
        self.assertEqual(self.element.current_index(), 1, 'default index is not set')

        # change the index of the GUI widget and check the element value
        self.gui._dropdown.setCurrentIndex(0)
        QTest.qWait(50)
        self.assertEqual(self.element.current_index(), 0)

@unittest.skip('')
class QtContainerIntegrationTest(unittest.TestCase):
    def setUp(self):
        config = {
            'label': 'Container!',
            'elements': [
                {
                    'type': 'label',
                    'label': 'hello there!',
                },
                {
                    'type': 'file',
                    'label': 'Select a file',
                },
            ]
        }
        self.element = elements.Container(config)
        self.gui = core.ContainerGUI(self.element)

    def test_setup(self):
        """Assert that the container builds correctly."""
        # assert the correct number of elements in the core container
        self.assertEqual(len(self.element._elements), 2)

        # assert the correct number of rows in the group's layout
        # Qt thinks there's always one extra row, hence the -1.
        self.assertEqual(self.gui.widgets.layout().rowCount() - 1, 2)

        # assert that the default is a non-collapsible container.
        self.assertEqual(self.element.is_collapsible(), False)
        self.assertEqual(self.gui.widgets.isCheckable(), False)

        # when the Container is not collapsible, I should not be able to
        # collapse it.
        self.assertRaises(elements.InteractionError,
            self.element.set_collapsed, True)

@unittest.skip('')
class QtCollapsibleContainerIntegrationTest(QtContainerIntegrationTest):
    def setUp(self):
        config = {
            'label': 'Container!',
            'collapsible': True,
            'elements': [
                {
                    'type': 'label',
                    'label': 'hello there!',
                },
                {
                    'type': 'file',
                    'label': 'Select a file',
                },
            ]
        }
        self.element = elements.Container(config)
        self.gui = core.ContainerGUI(self.element)

    def test_setup(self):
        """Assert that the container builds correctly."""
        # assert the correct number of elements in the core container
        self.assertEqual(len(self.element._elements), 2)

        # assert the correct number of rows in the group's layout
        # Qt thinks there's always one extra row, hence the -1.
        self.assertEqual(self.gui.widgets.layout().rowCount() - 1, 2)

        # assert that the default is a non-collapsible container.
        self.assertEqual(self.element.is_collapsible(), True)
        self.assertEqual(self.gui.widgets.isCheckable(), True)

    def test_collapsing(self):
        # assert that when the config defines that the element is collapsible,
        # the widget is indeed collapsible/checkable and that the container is
        # interactive to the user.
        self.assertEqual(self.gui.widgets.isCheckable(), True)
        self.assertEqual(self.gui.widgets.isEnabled(), True)

        # verify the default check state is unchecked
        self.assertEqual(self.gui.widgets.isChecked(), True)

        # verify that contained elements are enabled by default.
        for gui_elem, core_elem in zip(self.gui.elements, self.element.elements()):
            self.assertEqual(core_elem.is_enabled(), True)

            # if this is a primitive, elements are in a list.
            if type(gui_elem.widgets) is ListType:
                # loop through the list of widgets and assert each widget is
                # enabled.
                for qt_widget in gui_elem.widgets:
                    self.assertEqual(qt_widget.isEnabled(), True)

            else:
                # just access the widget directly and ensure it's enabled.
                self.assertEqual(gui_elem.widgets.isEnabled(), True)

            # assert that the palisades element is enabled and visible.
            self.assertEqual(core_elem.is_enabled(), True)
            self.assertEqual(core_elem.is_visible(), True)

        # Check the checkbox to close the container and ensure that the
        # checkbox_toggled signal is emitted.
        mock_function = mock.MagicMock(name='Function')
        self.gui.widgets.checkbox_toggled.register(mock_function)
        self.gui.widgets.setChecked(True)
        QTest.qWait(10)  # wait a few ms for event loop to notice, emit signal

        # assert that checking the container did what it was supposed to
        self.assertEqual(mock_function.called, True)  # verify signal emitted
        self.assertEqual(self.gui.widgets.isChecked(), True)  # box is checked

        # verify all contained elements and widgets are disabled, as expected.
        for gui_elem, core_elem in zip(self.gui.elements, self.element.elements()):
            self.assertEqual(core_elem.is_enabled(), False)

            # if this is a primitive, elements are in a list.
            if type(gui_elem.widgets) is ListType:
                # loop through the list of widgets and assert each widget is
                # enabled.
                for qt_widget in gui_elem.widgets:
                    self.assertEqual(qt_widget.isEnabled(), False)

            else:
                # just access the widget directly and ensure it's enabled.
                self.assertEqual(gui_elem.widgets.isEnabled(), False)

            # assert that the palisades element is disabled and invisible.
            self.assertEqual(core_elem.is_enabled(), False)
            self.assertEqual(core_elem.is_visible(), False)

        # re-open the container and verify all container elements are enabled in
        # Qt and visible (and enabled) in palisades.
        new_mock_function = mock.MagicMock(name='Function')
        self.gui.widgets.checkbox_toggled.register(new_mock_function)
        self.gui.widgets.setChecked(False)
        QTest.qWait(10)  # wait a few ms for event loop to notice, emit signal

        # assert that checking the container did what it was supposed to
        self.assertEqual(new_mock_function.called, True)  # verify signal emitted
        self.assertEqual(self.gui.widgets.isChecked(), False)  # box is checked

        # verify all contained elements and widgets are disabled, as expected.
        for gui_elem, core_elem in zip(self.gui.elements, self.element.elements()):
            self.assertEqual(core_elem.is_enabled(), True)

            # if this is a primitive, elements are in a list.
            if type(gui_elem.widgets) is ListType:
                # loop through the list of widgets and assert each widget is
                # enabled.
                for qt_widget in gui_elem.widgets:
                    self.assertEqual(qt_widget.isEnabled(), True)

            else:
                # just access the widget directly and ensure it's enabled.
                self.assertEqual(gui_elem.widgets.isEnabled(), True)

            # assert that the palisades element is disabled and invisible.
            self.assertEqual(core_elem.is_enabled(), True)
            self.assertEqual(core_elem.is_visible(), True)

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
        self.assertEqual(self.view._label.is_checked(), False)

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
        self.element = elements.File({})
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
