import os
import threading
import logging
from types import *

from palisades import fileio
from palisades import utils
from palisades.utils import Communicator
from palisades import validation
from palisades import execution
from palisades.i18n import translation
import palisades.gui
import palisades.i18n

LOGGER = logging.getLogger('elements')

class InvalidData(ValueError):
    def __init__(self, problem_data):
        ValueError.__init__(self)
        self.data = problem_data

    def __str__(self):
        return 'Inputs have errors: %s' % repr(self.data)

class ValidationStarted(RuntimeError): pass
class ElementDisabled(RuntimeError): pass
class InteractionError(RuntimeError): pass

def get_elements_list(group_pointer):
    """Construct a data structure with pointers to the elements of the group.

        group_pointer - a reference to a Group instance.

    Returns a list of elements and lists.  Example:
        [element, element, element, [element, element]]
    """
    #TODO: test this function.
    def _recurse_through_elements(elem_list):
        new_elements = []

        for elem in elem_list:
            if isinstance(elem, Primitive):
                new_elements.append(elem)
            else:
                new_elements.append(_recurse_through_elements,
                    elem.elements)
        return new_elements

    return _recurse_through_elements(group_pointer.elements)

# Assume this is a window for a moment.
class Application(object):
    def __init__(self, config_uri, lang_code='en'):
        # if GUI is None, have to visual display.
        # install the specified internal language.
        palisades.i18n.language.set(lang_code)
        configuration = translation.translate_json(config_uri, lang_code)
        self._window = Form(configuration)

class Element(object):
    """Element contains the core logic and interactivity required by all
    palisades element.

    Public Attributes:
        self.config - the rendered configuration options used by the Element
            class.  This is a dictionary containing at least default options.
        self.config_changed - a communicator.  Triggered when the
            configuration is changed.
        self.value_changed - a communicator.  Triggered when the value is
            changed.
        self.interactivity_changed - a communicator.  Triggered when the
            element's is either disabled or enabled.


    Private Attributes:
        self._enabled - boolean, indicates whether the element is enabled.
        self._parent_ui - a reference to the parent UI.
        self._default_config - a dictionary containing default configuration
            options.
    """
    defaults = {}

    def __init__(self, configuration, parent=None):
        object.__init__(self)
        self._enabled = True
        self._visible = True

        self._parent_ui = parent
        self._default_config = {}
        self._hashable_config = []  # keys corresponding to config keys to hash

        # Set up the communicators
        self.config_changed = Communicator()
        self.interactivity_changed = Communicator()
        self.visibility_changed = Communicator()

        # Render the configuration and save to self.config
        self.config = utils.apply_defaults(configuration, self.defaults)

    def set_default_config(self, new_defaults):
        """Add default configuration options to this Element instance's default
        config dictionary.  If this function is called after the element's UI
        representation is created, it will trigger the UI representation to
        reload the configuration.

        new_defaults - a python dictionary of default values.  Any duplicate keys
            contained in this new dictionary will overwrite existing defaults.

        Triggers the config_changed signal to be emitted with the new
        configuration.

        Returns nothing."""

        self._default_config.update(new_defaults)
        self.config = utils.apply_defaults(self.config, self._default_config)
        self.config_changed.emit(self.config)

    def is_enabled(self):
        """Query whether this element is enabled, indicating whether this
        element can be interacted with by the user.

        If this element is currently invisible, False will always be returned.

        Returns a boolean."""

        if self.is_visible():
            return self._enabled
        return False

    def set_enabled(self, new_state):
        """Enable or disable this element.

        new_state - A boolean.  If True, enable this element.  If False, disable
            this element.

        If the enabled state of this element changes, the interactivity_changed
        signal is emitted with the new state.

        Returns nothing."""

        new_state = bool(new_state)

        if new_state != self._enabled:
            self._enabled = new_state
            self.interactivity_changed.emit(new_state)

    def is_visible(self):
        """Query whether this element is visible and return the visibility
        state.

        Returns a boolean."""

        return self._visible

    def set_visible(self, new_visibility):
        """Show or hide this element to the user.

        new_visibility - a Boolean.  If True, show this element.  If False, hide
            this element.

        If the visibility of this element changes, the visibility_changed signal
        is emitted with the new visibility status.

        Note that making an element visible does not necessarily mean that it's
        interactive.  An element could be visible and noninteractive.  When an
        element is invisible, it is not interactive.

        Returns Nothing."""

        assert type(new_visibility) is BooleanType, 'Visibility must be True or False'

        # If visibility is changing, set the new visibility state and emit the
        # visibility_changed signal.
        if new_visibility != self.is_visible():
            self._visible = new_visibility
            self.visibility_changed.emit(self._visible)

    def set_state(self, state):
        raise Exception('Must be implemented for subclasses')

    def state(self):
        raise Exception('Must be implemented for subclasses')

    def _get_hashable_config(self):
        """Get the hashable configuration dictionary."""
        hashable_obj = {}
        for config_key, value in self.config.iteritems():
            if config_key in self._hashable_config:
                hashable_obj[config_key] = value

        # we always want to add certain object information, so add that here.
        hashable_obj['classname'] = self.__class__.__name__
        try:
            hashable_obj['args_id'] = self.config['args_id']
        except KeyError:
            # if there's no args_id for this element, skip it.
            pass

        LOGGER.debug('Hashable object: %s', hashable_obj)
        return hashable_obj

    def get_id(self, id_type='md5sum'):
        # md5sum represents a hash of relevant element attributes.
        # user represents the user-defined identifier, if provided (None if not
        # provided in JSON config)
        # TODO: make this work for Groups.
        assert id_type in ['md5sum', 'user']

        if id_type == 'md5sum':
            return utils.get_md5sum(self._get_hashable_config())
        else: # id type must be user-defined
            try:
                return self.config['id']
            except KeyError:
                # If the user did not specify an ID, then there is no user key.
                # when this happens, get the md5sum ID instead.
                return self.get_id('md5sum')

class Primitive(Element):
    """Primitive represents the simplest input element."""
    defaults = {
        'validateAs': {'type': 'disabled'},
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        Element.__init__(self, configuration)
        self._value = None

        # self._valid has 3 possible states:
        #   None -  indicates validation has not been performed on this value or
        #           else validation is in progress.
        #   True -  value passes validation.
        #   False - value fails validation (either validation failure or a
        #           warning)
        self._valid = None
        self._validation_error = None
        self._hashable_config = ['hideable', 'validateAs']

        # Set up our Communicator(s)
        self.value_changed = Communicator()
        self.validation_completed = Communicator()
        self.hidden_toggled = Communicator()

        # update the default configuration and set defaults based on the config.
        self.set_default_config(self.defaults)
        self._hidden = self.config['hideable']
        self._hideable = self.config['hideable']
        self._required = self.config['required']

        # Set up our validator
        self._validator = validation.Validator(
            self.config['validateAs']['type'])
        self._validator.finished.register(self._get_validation_result)

    def set_value(self, new_value):
        """Set the value of this element.  If the element's value changes, all
        registered callbacks will be emitted.

        Returns nothing."""


        LOGGER.debug('%s setting value to %s', self.get_id('user'), self._value)
        if not self.is_enabled():
            return

        # If the value of this element has changed, we want to trigger all the
        # elements that requested notification.
        old_value = self.value()
#        if old_value != new_value:
        self._value = new_value
        self._valid = None
        self.value_changed.emit(new_value)
        self.validate()

    def value(self):
        """Get the value of this element."""
        return self._value

    def is_valid(self):
        """Return the validity of this input.  If an element has not been
        validated, it will be validated here and will block until validation
        completes.  Returns a Boolean.
        """
        # If we don't know the validity and the validator has finished
        if self._valid == None and self._validator.thread_finished() == True:
            self.validate()

        self._validator.join()

        # Return whether validation passed (a boolean).
        if self.has_input():
            return self._valid
        else:
            if self.is_required():
                return self._valid
            else:
                return True  # if no input and optional, input is valid.

    def validate(self):
        # if validation is already in progress, block until finished.
        while not self._validator.thread_finished():
            pass

        validation_dict = self.config['validateAs'].copy()
        validation_dict['value'] = self.value()
        self._validator.validate(validation_dict)  # this starts the thread

    def _get_validation_result(self, error):
        """Utility class method to get the error result from the validator
        object.  Sets self._valid according to whether validation passed or
        failed, and sets the validation error to the error found (if any).

        error - a tuple of (error_msg, error_state)."""
        error_msg, state = error

        if state == validation.V_PASS:
            self._valid = True
        else:
            self._valid = False

        self._validation_error = error_msg
        self.validation_completed.emit(error)

    def is_hideable(self):
        return self._hideable

    def set_hidden(self, is_hidden):
        assert type(is_hidden) is BooleanType, ('is_hidden must be Boolean'
            ', %s found instead' % is_hidden.__class__.__name__)

        if self._hidden != is_hidden:
            self._hidden = is_hidden
            self.hidden_toggled.emit(is_hidden)

    def is_hidden(self):
        return self._hidden

    def state(self):
        """Return a python dictionary describing the state of this element."""
        state_dict = {
            'value': self.value(),
            'is_hidden': self.is_hidden()
        }
        return state_dict

    def set_state(self, state):
        """Set the state of this Element.

            state - a python dictionary defining the state of this element.
                Must have the following attributes:
                    'value' -> some pythonic value relevant to this element.
                    'is_hidden' -> a boolean.  Ignored if not hideable.
        """
        self.set_value(state['value'])
        self.set_hidden(state['is_hidden'])

    def is_required(self):
        return self._required

    def has_input(self):
        if self.value() != None:
            return True
        return False

    def should_return(self):
        LOGGER.debug('Checking whether should return: %s', self)
        # if element does not have an args_id, we're not supposed to return.
        # Therefore, return False.
        if 'args_id' not in self.config:
            LOGGER.debug('Element %s does not have an args_id', self)
            return False

        return_if_hidden = self.config['returns']['ifHidden']
        if return_if_hidden or self.is_hidden():
            LOGGER.debug('Element %s is hidden.', self)
            return False

        # if element is disabled and we're not supposed to return if disabled,
        # return False.
        return_if_disabled = self.config['returns']['ifDisabled']
        if self.is_enabled() is False:
            if return_if_disabled is False:
                LOGGER.debug('Element %s is disabled and should not return',
                    self)
                return False


        # if the element is empty and we're not supposed to return if it's
        # empty, return False.
        return_if_empty = self.config['returns']['ifEmpty']
        if not return_if_empty and not self.has_input():
            LOGGER.debug('Element %s (%s) is empty', self,
                    self.config['args_id'])
            return False

        # If none of the previous conditions have been met, return True.
        return True

    def help_text(self):
        """Returns the helpText attribute string."""
        return self.config['helpText']

class LabeledPrimitive(Primitive):
    defaults = {
        'label': u'',
        'validateAs': {'type': 'disabled'},
        'hideable': False,
        'required': False,
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        Primitive.__init__(self, configuration)
        self._hashable_config = ['hideable', 'validateAs', 'label']

        self.set_default_config(self.defaults)
        self._label = self.config['label']

    def set_label(self, new_label):
        cast_label = new_label.decode("utf-8")
        self._label = cast_label

    def label(self):
        return self._label

class Dropdown(LabeledPrimitive):
    defaults = {
        'options': ['No options specified'],
        'defaultValue': 0,
        'validateAs': {'type': 'disabled'},
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
            'type': 'strings'
        },
    }

    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self._hashable_config = ['hideable', 'validateAs', 'options',
            'label']

        self.set_default_config(self.defaults)
        assert self.config['returns']['type']in ['strings', 'ordinals'], (
            'the "returns" type key must be either "strings" or "ordinals", '
            'not %s' % self.config['returns'])

        self.options = self.config['options']
        self._value = self.config['defaultValue']

    def set_value(self, new_value):
        assert type(new_value) is IntType, ('Dropdown index must be an '
         'int, %s found' % new_value)
        assert new_value >= 0, 'Dropdown index must be >= 0'
        assert new_value < len(self.options), 'Dropdown index must exist'
        LabeledPrimitive.set_value(self, new_value)

    def current_index(self):
        """Return the current index (an int) of the dropdown."""
        return self._value

    def value(self):
        # if there are no options to select or the user has not selected an
        # option, return None.
        if len(self.options) is 0 or self._value is -1:
            return None

        # get the value of the currently selected option.
        return_option = self.config['returns']['type']
        if return_option == 'strings':
            return self.options[self._value]
        else:  # return option is 'ordinals'
            return self._value

    def state(self):
        state_dict = {
            'value': self._value,  # always return the current index
            'is_hidden': self.is_hidden()
        }
        return state_dict

class Text(LabeledPrimitive):
    defaults = {
        'width': 60,
        'defaultValue': '',
        'validateAs': {'type': 'string'},
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self._value = u""
        self.set_default_config(self.defaults)

        # Set the value of the element from the config's defaultValue.
        self.set_value(self.config['defaultValue'])

    def set_value(self, new_value):
        """Subclassed from LabeledPrimitive.set_value.  Casts all input values
        to utf-8.

            new_value - a python string.

        Returns nothing."""

        cast_value = unicode(new_value).decode('utf-8')
        LabeledPrimitive.set_value(self, cast_value)

    def has_input(self):
        if len(self.value()) > 0:
            return True
        return False

class File(Text):
    defaults = {
        'validateAs': {'type': 'file'},
        'defaultValue': u'',
        'width': 60,
        'label': u'',
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        Text.__init__(self, configuration)

        self.set_default_config(self.defaults)
        self.set_value(self.config['defaultValue'])

    def set_value(self, new_value):
        """Set the value of the File element.  All input values will be cast to
        UTF-8.

        new_value = a string, either a bytestring or unicode string.

        If new_value is relative to '~' (representing the user's home folder),
        the path will be expanded to be the absolute path of the value.
        Example: '~/some_file.txt' on linux might become
        '/home/username/some_file.txt'.  See the documentation for
        os.path.expanduser() for details about how this path is expanded.

        If the new value is a relative path (such as '../some_file.txt' or even
        just '.', indicating the current working directory), it will be expanded
        to be an absolute path based on the current working directory.

        NOTE: If you would like to clear the value of the field, use
        new_value=''.

        Returns nothing."""

        assert type(new_value) in [StringType, UnicodeType], ('New value must'
            'be either a bytestring or a unicode string, '
            '%s found.' % type(new_value))

        if new_value == '':
            # os.path.abspath('') is the same as os.getcwd(),
            # so I need to have a special case here.  If the user enters '.',
            # then the current dir will be used.
            absolute_path = ''
        else:
            absolute_path = os.path.abspath(os.path.expanduser(new_value))
        Text.set_value(self, absolute_path)

class Static(Primitive):
    def __init__(self, configuration):
        Primitive.__init__(self, configuration)
        self._hashable_config = ['returns']
        new_defaults = {
            'returns': None
        }

        self.set_default_config(new_defaults)

    def value(self):
        try:
            return self.config['defaultValue']
        except:
            pass
        return self.config['returns']

    def should_return(self):
        return True  # static should ALWAYS return.

    def state(self):
        return None

    def set_state(self, state):
        pass

    def is_valid(self):
        return True

class Label(Static):
    def __init__(self, configuration):
        Static.__init__(self, configuration)
        new_defaults = {
            'label': ''
        }
        self.set_default_config(new_defaults)

    def label(self):
        return self.config['label']

    def state(self):
        return

    def set_state(self, state):
        pass

class CheckBox(LabeledPrimitive):
    defaults = {
        'label': u'',
        'validateAs': {'type': 'disabled'},
        'hideable': False,
        'required': False,
        'helpText': "",
        'returns': {
            'ifDisabled': False,
            'ifEmpty': False,
            'ifHidden': False,
        },
    }

    def __init__(self, configuration):
        LabeledPrimitive.__init__(self, configuration)
        self._value = False  # initialize to be unchecked.

    def set_value(self, new_value):
        assert type(new_value) is BooleanType, ('new_value must be either True'
            ' or False, %s found' % type(new_value))
        LabeledPrimitive.set_value(self, new_value)

class Group(Element):
    def __init__(self, configuration, new_elements=None):
        Element.__init__(self, configuration)

        element_registry = {
            'file': File,
            'folder': File,
            'text': Text,
            'hidden': Static,
            'label': Label,
            'dropdown': Dropdown,
            'container': Container,
            'checkbox': CheckBox,
            'multi': Multi,
            'tab': Tab,
            'tabGroup': TabGroup,
        }

        if new_elements is not None:
            element_registry.update(new_elements)

        self._registrar = element_registry
        self._elements = []
        new_defaults = {
            'elements': [],
        }
        self.set_default_config(new_defaults)

        self.create_elements(self.config['elements'])
        self._display_label = True

    def _add_element(self, element):
        """Add the element to this group.

            element - an Element instance or subclass.

        Returns nothing."""
        self._elements.append(element)

    def create_elements(self, elements):
        """Create the elements contained by this group.

            elements - a list of dictionaries describing the elements to be
                created.

            Returns nothing."""
        for element_config in elements:
            try:
                new_element = self._registrar[element_config['type']](element_config)
            except KeyError as error:
                raise KeyError('%s not recognized as an acceptable element type' % error)
            LOGGER.debug('Creating new element %s', new_element)

            self._add_element(new_element)

    def elements(self):
        return self._elements

    def set_enabled(self, new_state):
        """Enable or disable this Group.  Disables all elements in the group
        as well as the Group itself.

        new_state - A boolean.  If True, enable this element.  If False, disable
            this element.

        If the enabled state of this element changes, the interactivity_changed
        signal is emitted with the new state.

        Returns nothing."""

        assert type(new_state) is BooleanType, ('New state must be a boolean, '
            '%s found instead.' % new_state.__type__.__name__)

        for element in self.elements():
            element.set_enabled(new_state)

        Element.set_enabled(self, new_state)

    def set_visible(self, new_visibility):
        """Set the visibility of this Group and all its sub_elements.

        new_visibility - a boolean.  If True, mark this element as visible.  If
            False, mark as invisible.  Applies to all sub-elements.

        Returns nothing."""

        assert type(new_visibility) is BooleanType, ('Visibility must be True'
            'or False, %s found' % type(new_visibility))

        for element in self.elements():
            element.set_visible(new_visibility)

        Element.set_visible(self, new_visibility)

    def state(self):
        """Returns a python dictionary with the relevant state of the Group (not
            including contained elements)."""
        state_dict = {
            'enabled': self.is_enabled(),
        }
        return state_dict

    def set_state(self, state):
        """Set the state of this group element.

            state - a python dictionary with these attributes;
                'enabled' -> a boolean
        """
        self.set_enabled(state['enabled'])

class Container(Group):
    """A Container is a special kind of Group that can enable or disable all its
    sub-elements."""
    def __init__(self, configuration, new_elements=None):
        Group.__init__(self, configuration, new_elements)
        new_defaults = {
            'label': '',
            'collapsible': False,
        }
        self.set_default_config(new_defaults)

        self._collapsible = self.config['collapsible']
        self._collapsed = False

        self.toggled = Communicator()

    def set_display_label(self, display):
        assert type(display) is BooleanType, 'display must be True or False'
        self._display_label = display

    def label(self):
        if self._display_label:
            return self.config['label']
        return ''

    def set_collapsed(self, is_collapsed):
        assert type(is_collapsed) is BooleanType

        # can only set as collapsed if container is collapsible
        if not self.is_collapsible():
            raise InteractionError("Container is not collapsible")

        self._collapsed = is_collapsed
        self.toggled.emit(is_collapsed)

        for element in self.elements():
            element.set_enabled(not is_collapsed)
            element.set_visible(not is_collapsed)

    def is_collapsible(self):
        return self._collapsible

    def is_collapsed(self):
        return self._collapsed

    def state(self):
        """Returns a python dictionary with the relevant state of the Group (not
            including contained elements)."""
        state_dict = Group.state(self)
        state_dict['collapsed'] = self.is_collapsed()
        return state_dict

    def set_state(self, state):
        """Set the state of this group element.

            state - a python dictionary with these attributes;
                'enabled' -> a boolean
                'collapsed' -> a boolean
        """
        if self.is_collapsible():
            self.set_collapsed(self.is_collapsed())
        Group.set_state(self, state)

class Multi(Container):
    def __init__(self, configuration, new_elements=None):
        Container.__init__(self, configuration, new_elements)
        new_defaults = {
            'label': '',
            'collapsible': False,
            'link_text': 'Add another',
            'helpText': "",
            'template': {
                'type': 'text',
                'label': 'Input a number',
                'validateAs': {'type': 'disabled'},
            },
        }

        # clean up unused configuration options inherited from Container
        # we have absolutely no interest in user-defined elements, since this
        # element only has elements created according to the template.
        # If any elements happen to have been created by the user, remove them
        # and log a warning.
        if len(self._elements) > 0:
            self._elements = []
            LOGGER.warn('Multi element does not currently support '
                ' non-template elements.  Elements found have been removed.')

        self.set_default_config(new_defaults)

        self.element_added = Communicator()
        self.element_removed = Communicator()

    def add_element(self, index=None):
        # need an optional argument for when an element is added by the
        # Container widget.
        self.create_elements([self.config['template']])
        new_index = len(self.elements()) - 1
        LOGGER.debug('Adding a new element at index %s', new_index)
        self.element_added.emit(new_index)  #index of element

    def remove_element(self, index):
        popped_element = self._elements.pop(index)
        self.element_removed.emit(index)

    def set_value(self, value_list):
        for value in value_list:
            self.add_element()
            self.elements()[-1].set_value(value)

    def value(self):
        return [e.value() for e in self.elements()]

    def state(self):
        state_dict = Container.state(self)
        state_dict['value'] = self.value()
        return state_dict

    def set_state(self, state):
        self.set_value(state['value'])
        Container.set_state(self, state)

class TabGroup(Group):
    def create_elements(self, elements):
        """Create elements after first asserting that all contained elements
        are tabs."""
        for element_config in elements:
            assert element_config['type'] == 'tab', ('Element type must be '
                '"tab", %s found instead' % element_config['type'])
        Group.create_elements(self, elements)

class Tab(Group):
    def __init__(self, configuration, new_elements=None):
        Group.__init__(self, configuration, new_elements)
        new_defaults = {
            'label': '',
        }
        self.set_default_config(new_defaults)

    def label(self):
        return self.config['label']

# The form class represents a single-window form where the user enters various
# inputs and then does something with them.  The IUI ModelUI would be an example
# of a form.
# Defining characteristics of a Form:
#  * contains a group of elements
#  * packages up required arguments from elements
#  * starts a model running when triggered.
class Form():
    def __init__(self, configuration):
        self._ui = Group(configuration)

        self.elements = self.find_elements()
        self.runner = None

        self.submitted = Communicator()

        # now that the form has been created, load the lastrun state, if
        # appliccable.
        try:
            self.load_state(self.lastrun_uri())
        except IOError:
            # when no lastrun file exists for this version
            LOGGER.warn('No lastrun file found at %s.  Skipping.',
                self.lastrun_uri())

    def find_elements(self):
        """Recurse through all elements in this Form's UI and locate all Element
        objects.

        Returns a list of element object references."""

        # TODO: if two elements have the same ID, raise an exception with a
        # helpful error message.
        all_elements = []

        def append_elements(element_list):
            for element in element_list:
                if isinstance(element, Group):
                    append_elements(element._elements)
                else:
                    all_elements.append(element)

        append_elements(self._ui._elements)
        return all_elements


    def collect_arguments(self):
        """Collect arguments from all elements in this form into a single
        dictionary in the form of {'args_id': value()}.  If an element does not
        have an args_id attribute, it is skipped.  Likewise, if an element
        should not be returned (if its should_return() function returns False),
        the element is skipped.

        Returns a python dictionary."""

        # Create the args dictionary and pass it back to the Application.
        args_dict = {}
        for element in self.elements:
            if element.should_return():
                args_dict[element.config['args_id']] = element.value()
            else:
                try:
                    args_id = element.config['args_id']
                except KeyError:
                    args_id = element.get_id('user')
                LOGGER.debug('Element %s should not return, skipping args_id %s',
                    element, args_id)
        return args_dict

    def save_state(self, uri):
        """Assemble the state of all elements and save them to a json object.

            uri - a URI to the file where the dictionary should be saved as JSON

            Returns nothing."""
        state_dict = {}
        for element in self.elements:
            element_id = element.get_id()
            element_state = element.state()
            try:
                element_state['_debug'] = element._get_hashable_config()
            except TypeError:
                # happens when element_state is None, which can happen when the
                # element is not a primitive.
                pass

            state_dict[element_id] = element_state

        utils.save_dict_to_json(state_dict, uri, 4)

    def load_state(self, state_uri):
        """Load a state from a file on disk.

            state_uri - a URI to a file on disk from where the Form's state can
                be loaded.

            Returns nothing."""
        form_state = utils.load_json(state_uri)
        for element in self.elements:
            element_id = element.get_id()

            # get the state of the element that matches this ID.
            try:
                element_state = form_state[element_id]
                element.set_state(element_state)
            except KeyError as missing_key:
                # When an ID key is missing, it means that the developer added
                # an element or else changed the element enough for it to not be
                # recognizeable to palisades.  When this happens, we can't set
                # the state, so log a warning and proceed.
                LOGGER.warn('Element ID %s does not have a saved state.',
                        missing_key)

    def lastrun_uri(self):
        """Fetch the URI for the internal lastrun save file."""
        if palisades.release == 'null':
            version_str = 'dev'
        else:
            version_str = palisades.__version__
        lastrun_filename = '%s_lastrun_%s.json' % (self._ui.config['modelName'],
            version_str)

        lastrun_uri = os.path.join(palisades.utils.SETTINGS_DIR, lastrun_filename)
        LOGGER.debug('Lastrun URI: %s', lastrun_uri)
        return lastrun_uri

    def submit(self, event=None):
        LOGGER.debug('Starting the form submission process')
        # Check the validity of all inputs
        form_data = []
        for element in self.elements:
            try:
                form_data.append((element.config['args_id'], element.is_valid(),
                    element.value()))
            except KeyError:
                # no attribute args_id, so skip.
                pass

        for element in form_data:
            print element

        form_is_invalid = False in [e[1] for e in form_data]

        # if success, assemble the arguments dictionary and send it off to the
        # base Application
        if form_is_invalid:
            invalid_inputs = []
            for args_id, is_valid, value in form_data:
                if not is_valid:
                    invalid_inputs.append((args_id, value))

            raise InvalidData(invalid_inputs)
        else:
            # save the current state of the UI to the lastrun location.
            self.save_state(self.lastrun_uri())

            args_dict = self.collect_arguments()

            # TODO: submit the args dict and other relevant data back to app.
            try:
                try:
                    function_name = self._ui.config['targetFunction']
                except KeyError:
                    function_name = 'execute'

                self.runner = execution.PythonRunner(self._ui.config['targetScript'],
                    args_dict, function_name)
                self.submitted.emit(True)
            except ImportError as error:
                LOGGER.error('Problem loading %s', self._ui.config['targetScript'])
                raise

            self.runner.start()


