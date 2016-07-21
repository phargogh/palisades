"""This module provides validation functionality for the palisades package.  In a
nutshell, this module will validate a value if given a dictionary that
specifies how the value should be validated."""

import csv
import os
import re
import sys
import time
import threading
import traceback

from osgeo import gdal
from osgeo import ogr

from palisades.utils import Communicator
from palisades.utils import RepeatingTimer

# TODO: make these constants used instead of string conventions
V_PASS = None
V_FAIL = 'fail'
V_ERROR = 'error'



class ValidationError(ValueError):
    """Custom validation error."""
    pass

# taken from iui/registrar.py
class Registrar(object):
    def __init__(self):
        object.__init__(self)
        self.map = {}

    def update_map(self, updates):
        self.map.update(updates)

    def eval(self, mapKey, opValues):
        try:
            return self.map[mapKey](opValues)
        except KeyError: #key not in self.map
            return None
        except ValueError as e:
            #This handles the case where a type is a numeric value but doens't cast
            #correctly.  In that case what is the value of an empty string?  Perhaps
            #it should be NaN?  Here we're returning 0.  James and Rich arbitrarily
            #decided this on 5/16/2012, there's no other good reason.
            if mapKey in ['int', 'float']:
                return 0
            else:
                # Actually print out the exception information.
                raise sys.exc_info()[1], None, sys.exc_info()[2]

    def get_func(self, mapKey):
        return self.map[mapKey]

class Validator(Registrar):
    """Validator class contains a reference to an object's type-specific
        checker.
        It is assumed that one single iui input element will have its own
        validator.

        Validation can be performed at will and is performed in a new thread to
        allow other processes (such as the UI) to proceed without interruption.

        Validation is available for a number of different values: files of
        various types (see the FileChecker and its subclasses), strings (see the
        PrimitiveChecker class) and numbers (see the NumberChecker class).

        element - a reference to the element in question."""

    def __init__(self, validator_type):
        #allElements is a pointer to a python dict: str id -> obj pointer.
        Registrar.__init__(self)

        updates = {'disabled': Checker,
                   'GDAL': GDALChecker,
                   'OGR': OGRChecker,
                   'number': NumberChecker,
                   'file': FileChecker,
                   'exists': URIChecker,
                   'folder': FolderChecker,
                   'DBF': DBFChecker,
                   'CSV': CSVChecker,
                   'table': FlexibleTableChecker,
                   'string': PrimitiveChecker}
        self.update_map(updates)
        self.type_checker = self.init_type_checker(str(validator_type))
        self.validate_funcs = []
        self.thread = None
        self.timer = None
        self.finished = Communicator()

    def add_validation(self, validation_callable, position):
        """Add a validation function or callable to the validation process."""

    def validate(self, valid_dict):
        """Validate the element.  This is a two step process: first, all
            functions in the Validator's validateFuncs list are executed.  Then,
            The validator's type checker class is invoked to actually check the
            input against the defined restrictions.

            Note that this is done in a separate thread.

            valid_dict - a python dictionary describing the validation to be
                performed.
            post_run=None - a python callable to be executed at the end of the
                validation thread.

            returns a string if an error is found.  Returns None otherwise."""

        if self.thread == None or not self.thread.is_alive():
            self.thread = ValidationThread(self.validate_funcs,
                self.type_checker, valid_dict)

            if self.timer != None and self.timer.is_alive:
                self.timer.cancel()
            self.timer = RepeatingTimer(0.01, self._check_thread)

        self.thread.start()
        self.timer.start()

    def _check_thread(self):
        """Private utility function to check on the state of the validation
        thread.  If it has finished, cancel the timer and emit the finished
        signal.  Returns nothing."""
        if self.thread_finished():
            self.timer.cancel()
            self.finished.emit(self.get_error())

    def join(self):
        """Block until all worker threads managed by Validator have finished.
            Returns nothing."""
        if self.thread is not None:
            self.thread.join()
            self.timer.join()
            time.sleep(0.01)  # sleep so timer definitely finishes executing.
        else:
            # in the case that validation has not been started, there's nothing
            # to join!
            return

    def thread_finished(self):
        """Check to see whether the validator has finished.  This is done by
        calling the active thread's is_alive() function.

        Returns a boolean.  True if the thread is alive."""

        if self.thread == None:
            return True
        return not self.thread.is_alive()

    def get_error(self):
        """Gets the error message returned by the validator.

        Returns a tuple with (error_state, error_message).  Tuple is (None,
        None) if no error has been found or if the validator thread has not been
        created."""

        if self.thread == None:
            return (None, None)
        return self.thread.get_error()

    def init_type_checker(self, validator_type):
        """Initialize the type checker based on the input validator_type.

            validator_type - a string representation of the validator type.

            Returns an instance of a checker class if validator_type matches an
                existing checker class.  Returns None otherwise."""

        try:
            return self.get_func(validator_type)()
        except KeyError:
            return None

class ValidationThread(threading.Thread):
    """This class subclasses threading.Thread to provide validation in a
        separate thread of control.  Functionally, this allows the work of
        validation to be offloaded from the user interface thread, thus
        providing a snappier UI.  Generally, this thread is created and managed
        by the Validator class."""

    def __init__(self, validate_funcs, type_checker, valid_dict):
        threading.Thread.__init__(self)
        self.validate_funcs = validate_funcs
        self.type_checker = type_checker
        self.valid_dict = valid_dict
        self.error_msg = None
        self.error_state = None

    def set_error(self, error, state='error'):
        """Set the local variable error_msg to the input error message.  This
        local variable is necessary to allow for another thread to be able to
        retrieve it from this thread object.

            error - a string.
            state - a python string indicating the kind of message being
                reported (e.g. 'error' or 'warning')

        returns nothing."""

        self.error_msg = error
        self.error_state = state

    def get_error(self):
        """Returns a tuple containing the error message and the error state,
        both being python strings.  If no error message is present, None is
        returned."""

        return (self.error_msg, self.error_state)

    def run(self):
        """Reimplemented from threading.Thread.run().  Performs the actual work
        of the thread."""

        for func in self.validate_funcs:
            error = func()
            if error != None:
                self.set_error(error)

        try:
            message = self.type_checker.run_checks(self.valid_dict)
            if message != '' and message != None:
                status = V_ERROR
            else:
                status = V_PASS
        except AttributeError:
            # Thrown when self.type_checker == None, set both message and
            # status to None.
            message = None
            status = V_PASS
        except Warning as warning:
            # Raised when an unexpected exception was raised by a validator.
            message = warning
            status = V_ERROR

        self.set_error(message, status)

class ValidationAssembler(object):
    """This class allows other checker classes (such as the abstract
    TableChecker class) to assemble sub-elements for evaluation as primitive
    values.  In other words, if an input validation dictionary contains two
    fields in a table, the ValidationAssembler class provides a framework to
    fetch the value from the table."""

    def __init__(self):
        object.__init__(self)
        self.primitive_keys = {'number': ['lessThan', 'greaterThan', 'lteq',
                                          'gteq'],
                               'string': []}

    def assemble(self, value, valid_dict):
        """Assembles a dictionary containing the input value and the assembled
        values."""
        assembled_dict = valid_dict.copy()
        assembled_dict['value'] = value

        if valid_dict['type'] in self.primitive_keys:
            assembled_dict.update(self._assemble_primitive(valid_dict))
        else:
            if 'restrictions' in valid_dict:
                assembled_dict.update(self._assemble_complex(valid_dict))

        return assembled_dict

    def _assemble_primitive(self, valid_dict):
        """Based on the input valid_dict, this function returns a dictionary
        containing the value of the comparator defined in valid_dict."""
        assembled_dict = valid_dict.copy()
        for attribute in self.primitive_keys[valid_dict['type']]:
            if attribute in valid_dict:
                value = valid_dict[attribute]
                if isinstance(value, str) or isinstance(value, unicode):
                    value = self._get_value(value)
                    assembled_dict[attribute] = value

        return assembled_dict

    def _assemble_complex(self, valid_dict):
        assembled_dict = valid_dict.copy()
        assembled_dict['restrictions'] = []

        for restriction in valid_dict['restrictions']:
            field_rest = restriction['validateAs']
            if self._is_primitive(field_rest):
                restriction['validateAs'] = self._assemble_primitive(field_rest)
                assembled_dict['restrictions'].append(restriction)

        return assembled_dict

    def _get_value(self, id):
        """Function stub for reimplementation.  Should return the value of the
        element identified by id, where the element itself depends on the
        context."""

        raise NotImplementedError

    def _is_primitive(self, valid_dict):
        """Check to see if a validation dictionary is a primitive, as defined by
        the keys in self.primitive_keys.

        valid_dict - a validation dictionary.

        Returns True if valid_dict represents a primitive, False if not."""
        if valid_dict['type'] in self.primitive_keys:
            return True
        return False

class Checker(Registrar):
    """The Checker class defines a superclass for all classes that actually
        perform validation.  Specific subclasses exist for validating specific
        features.  These can be broken up into two separate groups based on the
        value of the field in the UI:

            * URI-based values (such as files and folders)
                * Represented by the URIChecker class and its subclasses
            * Scalar values (such as strings and numbers)
                * Represented by the PrimitiveChecker class and its subclasses

        There are two steps to validating a user's input:
            * First, the user's input is preprocessed by looping through a list
              of operations.  Functions can be added to this list by calling
              self.add_check_function().  All functions that are added to this
              list must take a single argument, which is the entire validation
              dictionary.  This is useful for guaranteeing that a given function
              is performed (such as opening a file and saving its reference to
              self.file) before any other validation happens.

            * Second, the user's input is validated according to the
              validation dictionary in no particular order.  All functions in
              this step must take a single argument which represents the
              user-defined value for this particular key.

              For example, if we have the following validation dictionary:
                  valid_dict = {'type': 'OGR',
                                'value': '/tmp/example.shp',
                                'layers: [{layer_def ...}]}
                  The OGRChecker class would expect the function associated with
                  the 'layers' key to take a list of python dictionaries.

            """
    #self.map is used for restrictions
    def __init__(self):
        Registrar.__init__(self)
        self.checks = []
        self.ignore = ['type', 'value']
        self.value = None

    def add_check_function(self, func, index=None):
        """Add a function to the list of check functions.

            func - A function.  Must accept a single argument: the entire
                validation dictionary for this element.
            index=None - an int.  If provided, the function will be inserted
                into the check function list at this index.  If no index is
                provided, the check function will be appended to the list of
                check functions.

        returns nothing"""

        if index == None:
            self.checks.append(func)
        else:
            self.checks.insert(index, func)

    def run_checks(self, valid_dict):
        """Run all checks in their appropriate order.  This operation is done in
            two steps:
                * preprocessing
                    In the preprocessing step, all functions in the list of
                    check functions are executed.  All functions in this list
                    must take a single argument: the dictionary passed in as
                    valid_dict.

                * attribute validation
                    In this step, key-value pairs in the valid_dict dictionary
                    are evaluated in arbitrary order unless the key of a
                    key-value pair is present in the list self.ignore."""
        try:
            self.value = valid_dict['value']
            for check_func in self.checks:
                error = check_func(valid_dict)
                if error != None:
                    return error

            for key, value in valid_dict.iteritems():
                if key not in self.ignore and self.map[key] not in self.checks:
                    error = self.eval(key, value)
                    if error != None:
                        return error
        except Exception as e:
            print '%s: \'%s\' encountered, for input %s passing validation.' % \
                (e.__class__.__name__, e, valid_dict['value'])
            print traceback.format_exc()
            raise Warning('An unexpected error was encountered during' +
                          ' validation.  Use this input at your own risk.')
        return None


def check_filepath(path, mustExist=False, permissions='r'):
    if mustExist and not os.path.exists(path):
        raise ValidationError('Not found: %s', path)

    if permissions:
        if not os.path.exists(path):
            path = os.path.dirname(path)

        for letter, mode, descriptor in [
                ('r', os.R_OK, 'read'),
                ('w', os.W_OK, 'write'),
                ('x', os.X_OK, 'execute')]:
            if letter in permissions and not os.access(path, mode):
                raise ValidationError('You must have %s access to %s' %
                                      (descriptor, path))

def check_folder(path, mustExist=False, permissions='r', contains=None):
    check_filepath(path, mustExist, permissions)

    if contains:
        missing_files = []
        for relpath in contains:
            contained_filepath = os.path.join(path, relpath)
            if not os.path.exists(contained_filepath):
                missing_files.append(relpath)

        if missing_files:
            raise ValidationError('Directory %s is missing files: %s',
                                  (path, missing_files))


def check_raster(path):
    check_filepath(path, mustExist=True, permissions='r')

    gdal.PushErrorHandler('CPLQuietErrorHandler')
    dataset = gdal.Open(path)
    if not dataset:
        raise ValidationError('%s is not a GDAL-supported raster')


def check_number(num, gteq=None, greaterThan=None, lteq=None, lessThan=None,
                 allowedValues=None):

    num = float(num)

    if gteq != None and not num >= gteq:
        raise ValidationError('%s must be greater than or equal to %s' %
                              (num, gteq))
    if greaterThan != None and not num > greaterThan:
        raise ValidationError('%s must be greater than %s' % (num, greaterThan))
    if lteq != None and not num <= lteq:
        raise ValidationError('%s must be less than or equal to %s' %
                              (num, lteq))
    if lessThan != None and not num < lessThan:
        raise ValidationError('%s must be less than %s' % (num, lessThan ))

    # Allowed default pattern types:
    #  * Decimal (e.g. 4.333112)
    #  * Scientific (e.g. 4.E-170, 9.442e10)
    default_numeric_params = {
        'pattern': (
            r'^\s*'  # preceeding whitespace
            r'(-?[0-9]*(\.[0-9]*)?([eE]-?[0-9]+)?)'
            r'\s*$'),  # trailing whitespace
        'flag': None,
    }
    if allowedValues:
        default_numeric_params.update(allowedValues)

    check_regexp(str(num), **default_numeric_params)


def check_regexp(string, pattern='.*', flag=None):
    # Don't bother accepting  a regexp datastructure ... it's not used in
    # InVEST anyways and is easy enough to just write out.

    known_flags = {
        None: 0,  # Indicates no regex flags
        'ignoreCase': re.IGNORECASE,
        'verbose': re.VERBOSE,
        'debug': re.DEBUG,
        'locale': re.LOCALE,
        'multiline': re.MULTILINE,
        'dotAll': re.DOTALL,
    }

    if type(string) in [int, float]:
        string = str(string)

    matches = re.compile(pattern, known_flags[flag])
    if not matches.match(string):
        raise ValidationError('Value %s not allowed for pattern %s' %
                              (string, pattern))


def check_table_fields(table_fields, expected_fields):
    table_fields_set = set([f.upper() for f in table_fields])
    expected_fields_set = set([f.upper() for f in expected_fields])

    difference = expected_fields_set - table_fields_set
    if difference:
        raise ValidationError('Table is missing fields: %s' % list(difference))


def check_table_restrictions(row_dict, restriction_list):
    for restriction in restriction_list:
        field_details = restriction['field']
        if isinstance(field_details, basestring):
            # Then it's a fieldname
            label = field_details
            if field_details in row_dict:
                matching_fieldnames = [field_details]
            else:
                matching_fieldnames = []
        elif isinstance(field_details, dict):
            # If it's not a string, it's a dict that represents a regular
            # expression that could match many fields.
            label = field_details['pattern']
            regex = re.compile(field_details['pattern'])
            matching_fieldnames = []
            for key in row_dict:
                if type(key) in [int, float]:
                    key = str(key)

                if regex.match(key):
                    matching_fieldnames.append(key)
        else:
            raise Exception('Invalid field configuration: %s', field_details)

        try:
            if restriction['required'] and not matching_fieldnames:
                raise ValidationError('File is missing fields matching %s' %
                                      label)
        except KeyError:
            # field is not required by default, so ignore.
            pass

        for field in matching_fieldnames:
            restriction_type = restriction['validateAs']['type']
            restriction_params = restriction['validateAs'].copy()
            del restriction_params['type']

            if restriction_type == 'number':
                check_number(num=row_dict[field], **restriction_params)
            elif restriction_type == 'string':
                check_regexp(string=row_dict[field], **restriction_params)
            else:
                raise Exception('Unsupported restriction type %s' %
                                restriction_type)


def check_csv(path, fieldsExist=None, restrictions=None):
    # Before we actually open up the CSV for use, we need to check it for
    # consistency.  Specifically, all CSV inputs to InVEST must adhere to
    # the following:
    #    - All strings are surrounded by double-quotes
    #    - the CSV is comma-delimited.

    # using csv Sniffer not to see if it's a valid file, but to
    # determine the dialect.  csv.Sniffer requires that whole lines are
    # provided.
    with open(path, 'rbU') as csv_file:
        dialect = csv.Sniffer().sniff(
            '\n'.join(csv_file.readlines(1024)), delimiters=";,")
        csv_file.seek(0)
    opened_file = csv.DictReader(open(path), dialect=dialect)

    if fieldsExist:
        check_table_fields(opened_file.fieldnames, fieldsExist)

    if restrictions:
        for row_dict in opened_file:
            check_table_restrictions(row_dict, restrictions)


def check_vector(path, fieldsExist=None, restrictions=None, layers=None):
    check_filepath(path, mustExist=True, permissions='r')

    vector = ogr.Open(path)
    if not vector:
        raise ValidationError('Not a valid OGR vector: %s' % path)

    vector_fieldnames = [f.GetName() for f in vector.GetLayer().schema]

    if fieldsExist:
        check_table_fields(vector_fieldnames, fieldsExist)

    if restrictions:
        for layer_index, layer in enumerate(vector):
            for feature in layer:
                row_dict = dict((field, feature.GetField(field))
                                for field in vector_fieldnames)
                try:
                    check_table_restrictions(row_dict, restrictions)
                except ValidationError as validation_error:
                    raise ValidationError('Validation error in layer %s: %s' %
                                          (layer_index, validation_error))

    if layers:
        for layer_info in layers:
            layer_name = layer_info['name']
            if isinstance(layer_name, dict):
                # dict here represents {'inheritFrom': 'file'}.  The form is
                # inconsequential, it just means that we use the first layer
                # available.
                layer = vector.GetLayer(0)
                layer_name = layer.GetName()
            else:
                layer = vector.GetLayerByName(layer_name)

            if not layer:
                raise ValidationError('Vector is missing layer %s' %
                                      layer_name)

            reference = layer.GetSpatialRef()
            if 'projection' in layer_info:
                if not reference:
                    raise ValidationError('Could not read spatial reference '
                                          'information from vector')

                if 'units' in layer_info['projection']:
                    linear_units = reference.GetLinearUnitsName().lower()

                    # keys are JSON-understood projection units
                    # values are known projection wkt equivalents
                    known_units = {
                        'meters':  ['meter', 'metre'],
                        'US Feet': ['foot_us']
                    }

                    # NOTE: If the JSON-defined linear unit (the expected unit)
                    # is not in the known_units dictionary, this will
                    # throw a keyError, which causes a validation error to be
                    # printed.
                    required_unit = layer_info['projection']['units']
                    try:
                        expected_units = known_units[required_unit]
                    except:
                        raise ValidationError(
                            'Expected projection units must be '
                            'one of %s, not %s' % (known_units.keys(),
                                                   required_unit))

                    if linear_units not in expected_units:
                        raise ValidationError((
                            'Vector layer %s must be projected '
                            'in %s (one of %s, case-insensitive). \'%s\' '
                            'found.') % (layer_name, required_unit,
                                expected_units, linear_units))

                # Validate whether the layer should be projected
                projection = reference.GetAttrValue('PROJECTION')
                if 'exists' in layer_info['projection']:
                    should_be_projected = layer_info['projection']['exists']
                    if bool(projection) != should_be_projected:
                        if not should_be_projected:
                            negate_string = 'not'
                        else:
                            negate_string = ''
                        raise ValidationError((
                            'Vector layer %s should %s be ' +
                            'projected') % (layer_name, negate_string))

                # Validate whether the layer's projection matches the
                # specified projection
                if 'name' in layer_info['projection']:
                    projection_name = layer_info['projection']['name']
                    if projection != projection_name:
                        raise ValidationError(
                            'Shapefile layer %s must be '
                            'projected as %s' % (layer_name, projection_name))

            if 'datum' in layer_info:
                datum = reference.GetAttrValue('DATUM')
                if datum != layer_info['datum']:
                    raise ValidationError(
                        'Vector layer %s must have the datum %s' % (
                            layer_name, layer_info['datum']))
