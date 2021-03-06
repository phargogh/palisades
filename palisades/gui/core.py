import logging
import platform
import subprocess
import os
import code
import time
import sys
import traceback

os.environ['QT_API'] = 'PyQt4'

import palisades.gui
import palisades.i18n
from palisades import elements
from palisades.gui import qt4 as toolkit
from palisades.validation import V_ERROR
from palisades.validation import V_FAIL
from palisades.validation import V_PASS
from palisades.elements import InvalidData, WorkspaceExists

class NotYetImplemented(Exception): pass

LOGGER = logging.getLogger('palisades.gui.core')
_ = palisades.i18n.language.ugettext

def _print_obj_debug(obj):
    print '#' * 40
    print 'Debug:'
    print '-' * 12
    print ''
    print 'class %20s' % str(obj)
    print 'classname %20s' % obj.__class__.__name__
    print ''

def explore_folder(dirname):
    """Open a folder in the user's operating system's native file explorer.

    Returns nothing."""

    LOGGER.debug("Opening dirname %s", dirname)
    #Try opening up a file explorer to see the results.
    try:
        LOGGER.info('Opening file explorer to workspace directory')
        if platform.system() == 'Windows':
            # Try to launch a windows file explorer to visit the workspace
            # directory now that the operation has finished executing.
            LOGGER.info('Using windows explorer to view files')
            subprocess.Popen('explorer "%s"' % os.path.normpath(dirname))
        elif platform.system() == 'Darwin':
            LOGGER.info('Using mac finder to view files')
            subprocess.Popen('open %s' % os.path.normpath(dirname), shell=True)
        else:
            # Assume we're on linux.  No biggie, just use xdg-open to use the
            # default file opening scheme.
            LOGGER.info('Not on windows or mac, using default file browser')
            subprocess.Popen(['xdg-open', dirname])
    except OSError as error:
        # OSError is thrown if the given file browser program (whether
        # explorer or xdg-open) cannot be found.  No biggie, just pass.
        LOGGER.error(error)
        LOGGER.error('Cannot find default file browser. Platform: %s |' +
            ' folder: %s', platform.system(), dirname)

def printstacks():
    print >> sys.stderr, "\n*** STACKTRACE - START ***\n"
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# ThreadID: %s" % threadId)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))

    for line in code:
        print >> sys.stderr, line
    print >> sys.stderr, "\n*** STACKTRACE - END ***\n"


class ApplicationGUI(object):
    def __init__(self):
        object.__init__(self)
        self.app = toolkit.Application()
        self.windows = []
        self.window = None
        self.splashscreen = None

    def add_window(self, form_ptr):
        """Add a window with the appropriate structure of elements.  Assume it's
        a form for now."""
        self.window = FormGUI(form_ptr)
        self.windows.append(self.window)

    def show_splash(self, img_uri):
        self.splashscreen = toolkit.SplashScreen(img_uri)
        self.splashscreen.show()
        self.splashscreen.show_message(_('Starting ...'))

    def set_splash_message(self, splash_msg):
        self.splashscreen.clear_message()
        self.splashscreen.show_message(splash_msg)

    def find_input(self, id):
        """Locate an element in any of the windows in this application that has
        a core element ID matching `id`.  Raises a KeyError if none are found.
        Returns an object pointer to the GUI object of the first match found."""
        for window in self.windows:
            try:
                return window.find_input(id)
            except KeyError:
                pass
        raise KeyError(id)

    def execute(self, interactive=False):
        self.app.process_events()
        for window in self.windows:
            window.show()
            self.app.process_events()

        if self.splashscreen is not None:
            self.splashscreen.show_message(_('Ready!'))
            self.splashscreen.finish(self.windows[0].window, 1)

        if interactive:
            code.interact(
                banner=('Palisades Debug Shell\n'
                        "Globals:\n"
                        "  form - The form element object\n"
                        "  gui  - The gui representation of the form\n"
                        "  printstacks - print current threadstacks\n"
                        "NOTE: Terminating the shell terminates the "
                        "application."),
                local={
                    'form': self.window.element,
                    'gui': self.window,
                    'printstacks': printstacks,
                })
        else:
            self.app.execute()

    def exit(self):
        self.app.exit()

class UIObject(object):
    def __init__(self, core_element):
        self.element = core_element

        self.element.visibility_changed.register(self.set_visible)
        self.element.interactivity_changed.register(self.set_enabled)

    def set_visible(self, is_visible):
        """Update the element's visibility in the toolkit."""
        _print_obj_debug(self)
        raise NotYetImplemented

    def set_enabled(self, is_enabled):
        """Update the element's interactivity in the toolkit"""
        _print_obj_debug(self)
        raise NotImplementedError

class GroupGUI(UIObject):
    def __init__(self, core_element, registrar=None):
        UIObject.__init__(self, core_element)

        #TODO: add all the necessary elements here to the form.
        registry = {
            'File': FileGUI,
            'Folder': FileGUI,
            'Text': TextGUI,
            'Group': GroupGUI,
            'Label': LabelGUI,
            'Static': None,  # None means no GUI display.
            'Dropdown': DropdownGUI,
            'TableDropdown': DropdownGUI,
            'OGRFieldDropdown': DropdownGUI,
            'Container': ContainerGUI,
            'CheckBox': CheckBoxGUI,
            'Multi': MultiGUI,
            'Tab': TabGUI,
            'TabGroup': TabGroupGUI,
        }

        if registrar != None:
            assert isinstance(registrar, dict)
            registry.update(registrar)

        self.registrar = registry

        # If a subclass has already set up a toolkit widget for this object, we
        # want to use that widget.  Assumes that the widget is a subclass of
        # toolkit.Group.
        if not hasattr(self, 'widgets'):
            self.widgets = toolkit.Group()

        self.elements = []

        # create the elements here.  Elements should probably only ever be
        # created once, not dynamically (though they could be hidden/revealed
        # dynamically), so no need for a separate function.
        for element in core_element._elements:
            self.add_view(element)

    def add_view(self, element):
        # get the correct element type for the new object using the new
        # element's object's string class name.
        # TODO: if element is a Group, it must create its contained widgets
        try:
            element_classname = element.__class__.__name__
            try:
                cls = self.registrar[element_classname]
            except KeyError as missing_key:
                raise KeyError('%s not a recognized GUI type' % missing_key)

            if element_classname in ['Group', 'Container', 'TabGroup', 'Tab']:
                new_element = cls(element, self.registrar)
            else:
                new_element = cls(element)
        except TypeError as error:
            # Happens when the element's GUI representation in registry is
            # None, meaning that there should not be a GUI display.
            LOGGER.warning('No graphical representation known for %s: %s',
                element_classname, error)
            new_element = None

        # If the new element is None, there's no visualization.  Skip.
        # new_element is the GUI representation of a palisades Element.
        # TODO: create a better naming scheme for each layer.
        if new_element is not None:
            self.widgets.add_widget(new_element)
            self.elements.append(new_element)

    def set_visible(self, is_visible):
        """Set the visibility of this element."""
        self.widgets.set_visible(is_visible)

    def set_enabled(self, is_enabled):
        """Set the interactivity of this element."""
        self.widgets.set_enabled(is_enabled)

class TabGroupGUI(GroupGUI):
    def __init__(self, core_element, registrar=None):
        if not hasattr(self, 'widgets'):
            self.widgets = toolkit.TabGroup()
        GroupGUI.__init__(self, core_element, registrar)


class TabGUI(GroupGUI):
    def __init__(self, core_element, registrar=None):
        if not hasattr(self, 'widgets'):
            self.widgets = toolkit.Group()
        GroupGUI.__init__(self, core_element, registrar)

    def label(self):
        return self.element.label()


class ContainerGUI(GroupGUI):
    def __init__(self, core_element, registrar=None):
        # TODO: find a better way to specify the toolkit widget.
        if not hasattr(self, 'widgets'):
            self.widgets = toolkit.Container(core_element.label())

        GroupGUI.__init__(self, core_element, registrar)
        self.widgets.set_collapsible(self.element.is_collapsible())

        # initialize the collapsed state to mirror the state of the UI.
        self.widgets.set_collapsed(self.element.is_collapsed())
        for gui_elem in self.elements:
            gui_elem.set_visible(not self.element.is_collapsed())

        # when the container is collapsed by the GUI user, set the underlying
        # element to be collapsed
        self.widgets.checkbox_toggled.register(self.element.set_collapsed)

        # when the container is collapsed by the python core, collapse the GUI
        # container
        self.element.toggled.register(self._set_collapsed)

        # Initialize the interactivity state
        self.widgets.set_enabled(self.element.is_enabled())

    def _set_collapsed(self, event=None):
        self.widgets.set_collapsed(self.element.is_collapsed())

        for gui_elem in self.elements:
            gui_elem.set_visible(not self.element.is_collapsed())
            gui_elem.set_enabled(not self.element.is_collapsed())

class MultiGUI(ContainerGUI):
    def __init__(self, core_element, registrar=None):
        # TODO: find a better way to specify the toolkit widget.
        # TODO: implement a way to access link_text without going into config
        self.widgets = toolkit.Multi(core_element.label(),
                core_element.config['link_text'])
        ContainerGUI.__init__(self, core_element, registrar)

        self.widgets.element_requested.register(self.element.add_element)
        self.element.element_added.register(self._add_element)
#        self.widgets.element_removed.register(self.element.remove_element)
        self.widgets.element_removed.register(self._remove_element)

    def _remove_element(self, index):
        # remove the target element from the internal elements list and call
        # the element's remove_element function.
        removed_element = self.elements.pop(index)
        self.element.remove_element(index)

    def _add_element(self, new_index):
        # index is the row index of the new element.
        new_element = self.element.elements()[new_index]
        self.add_view(new_element)
        # TODO: emit a communicator here??

class PrimitiveGUI(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)
        self.widgets = []
        self._visible = True
        self._enabled = True
        self.set_enabled(self.element.is_enabled())

    def set_visible(self, is_visible):
        self._visible = is_visible
        for widget in self.widgets:
            widget.set_visible(is_visible)

    def is_visible(self):
        return self._visible

    def is_enabled(self):
        return self._enabled

    def set_enabled(self, is_enabled):
        self._enabled = is_enabled
        for widget in self.widgets:
            widget.set_enabled(is_enabled)

class LabeledPrimitiveGUI(PrimitiveGUI):
    def __init__(self, core_element):
        PrimitiveGUI.__init__(self, core_element)

        label_text = self.element.label()
        if self.element.is_hideable():
            self._label = toolkit.CheckBox(label_text)
            self._label.checkbox_toggled.register(self._toggle_widgets)
            self._label.set_checked(not self.element.is_hidden())
            self._toggle_widgets(False)
        else:
            self._label = toolkit.ElementLabel(label_text)

        self._validation_button = toolkit.ValidationButton(label_text)
        self._help_button = toolkit.InformationButton(label_text)
        self._help_button.set_body(self.element.help_text())

        self.widgets = [
            self._validation_button,
            self._label,
            toolkit.Empty(),
            toolkit.Empty(),
            self._help_button,
        ]
        # We modified local widgets, so we need to restore the correct enable
        # state
        self.set_enabled(self.element.is_enabled())

    # TODO: make this set the active widget.
    # I'm thinking of a function to set the active input widget, but you could
    # also pass in the target Communicator to be connected and the function to
    # be registered with the Communicator.
    def set_widget(self, index, new_widget):
        self.widgets[index] = new_widget

    def _toggle_widgets(self, show):
        """Show or hide the widgets in this view."""
        # show must be boolean.
        for widget in self.widgets:
            if widget != self._label:
                widget.set_visible(show)

        self.element.set_hidden(not show)

        if not show:
            # clear the error state of the label
            self._label.set_error(False)

class CheckBoxGUI(LabeledPrimitiveGUI):
    def __init__(self, core_element):
        LabeledPrimitiveGUI.__init__(self, core_element)

        # Checkbox widget with no label ... the label is managed by the
        # LabeledPrimitiveGUI class.
        self._checkbox = toolkit.CheckBox('')
        self.set_widget(2, self._checkbox)
        self._checkbox.set_checked(self.element.value())

        # when the checkbox is checked by the user, set the value of the
        # underlying element object.
        self._checkbox.checkbox_toggled.register(self.element.set_value)
        # I'm deliberately not caring about validation here because a checkbox
        # should not be validated (as far as I can tell).
        # TODO: Should a checkbox be able to be validated?  If so, how to show?

class TextGUI(LabeledPrimitiveGUI):
    def __init__(self, core_element):
        LabeledPrimitiveGUI.__init__(self, core_element)

        # Convert int/float types to bytestring.  String output of text
        # elements should already be UTF-8
        element_value = self.element.value()
        if type(element_value) in [float, int]:
            element_value = str(element_value)

        self._text_field = toolkit.TextField(element_value)
        self.set_widget(2, self._text_field)

        # when the text is modified in the textfield, call down to the element
        # to set the text
        self._text_field.value_changed.register(self.element.set_value)

        # when the core element's value is changed, update the value of the
        # gui element.
        self.element.value_changed.register(self._text_field.set_text)

        # when the user requests a reset on the value, oblige.
        self._text_field.reset_requested.register(self._reset_value)

        self.element.validation_completed.register(self._update_validation)
        self.set_enabled(self.element.is_enabled())

    def _reset_value(self, event=None):
        self.element.reset_value()

    def _update_validation(self, error_state):
        """Update the visual validation state.  The validation result is
        ignored if the element is optional and has no input.  Otherwise, the
        element's validation satate is observed."""
        if self.element.has_input():
            error_msg, error = error_state
            active = True
            if error == V_FAIL:
                error = 'error'
        else:
            if self.element.is_required():
                error = V_ERROR
                error_msg = _('Element is required')
                active = True
            else:
                error = V_PASS
                error_msg = _('(Element is optional)')
                active = False

        if error == None:
            error = 'pass'

        if error_msg == None:
            error_msg = ''

        self._validation_button.set_error(error_msg, error)
        self._validation_button.set_active(active)
        self._text_field.set_error(error == V_ERROR)
        self._label.set_error(error == V_ERROR)

class FileGUI(TextGUI):
    def __init__(self, core_element):
        TextGUI.__init__(self, core_element)

        self._text_field = toolkit.FileField(self.element.value())
        self.set_widget(2, self._text_field)
        self._text_field.clicked.register(self._file_requested)
        self._text_field.value_changed.register(self.element.set_value)

        # when the text is modified in the textfield, call down to the element
        # to set the text
        self._text_field.value_changed.register(self.element.set_value)

        # when the user requests a reset on the value, oblige.
        self._text_field.reset_requested.register(self._reset_value)

        # when the element's core value is changed, update the value of the gui
        # element.
        self.element.value_changed.register(self._text_field.set_text)

        # create the FileButton using the 'type' attribute, one of file or
        # folder
        self._file_button = toolkit.FileButton(self.element.config['type'],
            self._text_field, self.element.config['label'])
        self._file_button.file_selected.register(self._file_selected)
        self.set_widget(3, self._file_button)
        self.set_enabled(self.element.is_enabled())

    def _file_requested(self, event=None):
        if len(self.element.value()) == 0:
            self._file_button._get_file()

    def _file_selected(self, new_value):
        # set the textfield's value
        self._text_field.set_text(new_value, force=True)

        # set the core element's value
        self.element.set_value(new_value)

class DropdownGUI(LabeledPrimitiveGUI):
    def __init__(self, core_element):
        LabeledPrimitiveGUI.__init__(self, core_element)

        if isinstance(core_element, elements.TableDropdown):
            # TableDropDowns won't have their columns until they are loaded
            # from their target file.
            current_index = -1
        else:
            current_index = self.element.current_index()

        self._dropdown = toolkit.Dropdown(self.element.options,
            current_index)
        self.set_widget(2, self._dropdown)

        self._dropdown.value_changed.register(self.element.set_value)
        self.element.options_changed.register(self._load_options)

        # We modified local widgets, so we need to restore the correct enable
        # state
        self.set_enabled(self.element.is_enabled())

    def _load_options(self, new_options):
        self._dropdown.load_options(new_options)
        try:
            current_index = self.element.current_index()
        except ValueError as e:
            print e
            current_index = -1

        print 'OPTIONS', current_index
        self._dropdown.set_index(current_index)
        self.set_enabled(self.element.is_enabled())

class LabelGUI(UIObject):
    def __init__(self, core_element):
        UIObject.__init__(self, core_element)
        self.widgets = toolkit.Label(self.element.label(),
                                     core_element.styles())
        self.element.label_changed.register(self._reload_label)
        self.element.styles_changed.register(self._reload_label)

    def set_visible(self, is_visible):
        self.widgets.set_visible(is_visible)

    def set_enabled(self, is_enabled):
        self.widgets.set_enabled(is_enabled)

    def _reload_label(self, event_data=None):
        self.widgets.set_styles(self.element.styles())
        self.widgets.set_label(self.element.label())


class FormGUI():
    LOG_FMT = "%(asctime)s %(name)-18s %(levelname)-8s %(message)s"
    DATE_FMT = "%m/%d/%Y %H:%M:%S "

    def __init__(self, core_element):
        self.element = core_element

        self.langs = self.element.langs

        self.group = GroupGUI(self.element._ui)
        self.window = toolkit.FormWindow(self.group.widgets, self.element.title())
        self.window.set_langs(self.langs)
        self.quit_confirm = toolkit.ConfirmQuitDialog()
        self.errors_dialog = toolkit.ErrorDialog()
        self.messages_dialog = toolkit.RealtimeMessagesDialog(
            window_title="Running " + self.element.title())
        self.file_dialog = toolkit.FileDialog()
        self.workspace_confirm_dialog = toolkit.WarningDialog()

        self.messages_handler = logging.StreamHandler(self.messages_dialog)
        self.messages_formatter = logging.Formatter(self.LOG_FMT, self.DATE_FMT)
        self.messages_handler.setFormatter(self.messages_formatter)

        self.window.submit_pressed.register(self.submit)
        self.window.quit_requested.register(self.close)
        self.window.reset_requested.register(self.reset)
        self.element.submitted.register(self.messages_dialog.start)
        self.element.submitted.register(self._open_messages_window)

        #TODO: Add more communicators here ... menu item actions?
        self.window.load_params_request.register(self._load_params)
        self.window.save_params_request.register(self._save_params)
        self.window.save_python_request.register(self._save_python)
        self.messages_dialog.dir_open_requested.register(
            self._open_workspace_if_finished)

    def find_input(self, id):
        """Recurse through all inputs in this form and locate the GUI object
        that is linked to the element with `id` as the element id.  Returns a
        GUI element, or raises a KeyError if not found."""
        known_elements = {}
        def _locate(element):
            known_elements[element.element.get_id('user')] = element
            if isinstance(element, GroupGUI):
                for contained_element in element.elements:
                    _locate(contained_element)

        _locate(self.group)
        return known_elements[id]

    def _load_params(self, event=None):
        param_file = self.file_dialog.get_file('parameter file')

        if param_file != '':
            self.element.load_state(param_file)

    def _save_params(self, event=None):
        try:
            model_name = self.element._ui.config['modelName']
            model_name += '_saved.json'
        except KeyError:
            model_name = 'saved_run.json'

        param_file = self.file_dialog.get_file('parameter file', save=True,
            savefile=model_name)

        if param_file != '':
            self.element.save_state(param_file)

    def _save_python(self, event=None):
        # get the errors that exist from the underlying form
        # only save the python file if there are no errors.
        if not self.element.form_is_valid():
            self.errors_dialog.set_messages(self.element.form_errors())
            self.errors_dialog.show()
        else:
            python_file = self.file_dialog.get_file('new python file', save=True)
            if python_file != '':
                self.element.save_to_python(python_file)

    def submit(self, event=None):
        """
        Callback to check for errors and submit unless there are errors in the
        form.
        """
        try:
            self.element.submit()
            errors = []
        except WorkspaceExists as workspace_path:
            self.workspace_confirm_dialog.set_title(_('Output Exists'))
            self.workspace_confirm_dialog.set_body_text(_(
                'The directory {workspace} exists and contains files '
                'that may be overwritten.  Continue?').format(
                    workspace=workspace_path))

            # PROMPT FOR USER CONFIRMATION
            # 1 indicates user acceptance.
            # 0 indicates rejcection/cancellation.
            self.workspace_confirm_dialog.exit_code = None
            self.workspace_confirm_dialog.confirm()  # non-blocking
            while self.workspace_confirm_dialog.exit_code is None:
                time.sleep(0.1)

            if self.workspace_confirm_dialog.exit_code == 0:
                # Returning will prevent the form from being submitted.
                return

            self.element.submit(workspace_can_exist=True)

        except InvalidData as error:
            errors = error.data[:]
            self.errors_dialog.set_messages(errors)
            self.errors_dialog.show()
            return

        self.element.runner.finished.register(self._runner_finished)

    def _open_messages_window(self, event=None):
        self.messages_dialog.show()
        self.element.runner.executor.log_manager.add_log_handler(
            self.messages_handler, filter_palisades=True)

    def _runner_finished(self, thread_name, thread_failed, thread_traceback):
        if thread_failed:
            self.messages_dialog.finish(thread_failed,
                self.element.runner.executor.exception)
        else:
            self.messages_dialog.finish(False)
            if self.messages_dialog.workspace_open_requested():
                explore_folder(self.element.get_target_workspace())

    def _open_workspace_if_finished(self, event=None):
        if self.element.runner.is_finished():
            if self.messages_dialog.workspace_open_requested():
                explore_folder(self.element.get_target_workspace())

    def show(self):
        self.window.show()

    def close(self, data=None):
        self.quit_confirm.confirm()
        while self.quit_confirm.exit_code is None:
            time.sleep(0.1)

        if self.quit_confirm.exit_code != 0:
            self.window.close()

    def reset(self, data=None):
        self.element.reset_values()
